#!/usr/bin/env python3
"""
A small financial crimes alerting demo.

It makes up 90 days of bank transactions for a few dozen customers, hides five
suspicious customers among them, then runs five simple AML rules over the data
and prints the alerts they raise. Everything is fake.

    python3 alerting_demo.py                 run the rules and show the alerts
    python3 alerting_demo.py --customer C-101  show one customer's transactions
    python3 alerting_demo.py --csv alerts.csv  also save the alerts to a CSV file

Try changing the numbers in THRESHOLDS below and running it again: that is
"tuning", and you will see alerts appear and disappear.
"""

import argparse
import csv
import random
from collections import defaultdict
from datetime import date, timedelta

# The knobs. Real banks spend a lot of time choosing these numbers.
THRESHOLDS = {
    "cash_reporting_limit": 10_000,   # cash deposits at or above this are reported anyway
    "structuring_near_limit": 0.85,   # "just under" means at least 85% of the limit
    "structuring_min_count": 3,       # how many near-limit deposits...
    "structuring_window_days": 7,     # ...within how many days
    "pass_through_min_amount": 20_000,
    "pass_through_out_share": 0.80,   # at least 80% of it leaves again...
    "pass_through_window_days": 3,    # ...within this many days
    "high_risk_min_amount": 5_000,
    "dormant_days": 60,               # no activity for this long counts as dormant
    "dormant_wake_amount": 15_000,
    "out_of_profile_multiple": 5,     # a month 5x bigger than the customer said to expect
}

# Made-up country names so we are not labelling real places.
HIGH_RISK_COUNTRIES = {"Ruritania", "Freedonia"}
NORMAL_COUNTRIES = ["UK", "UK", "UK", "UK", "France", "Ireland", "Spain", "USA"]

START = date(2026, 7, 27)
DAYS = 90


# ---------------------------------------------------------------------------
# Step 1: make up some data
# ---------------------------------------------------------------------------

def make_customers(rng):
    """Normal customers, each with how much money they told the bank to expect per month."""
    jobs = [("Teacher", 3_000), ("Nurse", 3_200), ("Shop owner", 15_000), ("Engineer", 5_000),
            ("Retired", 2_000), ("Plumber", 6_000), ("Café owner", 12_000), ("Accountant", 5_500)]
    customers = {}
    for n in range(1, 41):
        job, expected = rng.choice(jobs)
        customers[f"C-{n:03d}"] = {"job": job, "expected_monthly": expected}
    # The five planted suspicious customers
    customers["C-101"] = {"job": "Taxi driver", "expected_monthly": 4_000}
    customers["C-102"] = {"job": "Consultant", "expected_monthly": 8_000}
    customers["C-103"] = {"job": "Importer", "expected_monthly": 20_000}
    customers["C-104"] = {"job": "Retired", "expected_monthly": 1_500}
    customers["C-105"] = {"job": "Student", "expected_monthly": 800}
    return customers


def tx(day, customer, kind, direction, amount, country="UK"):
    """One transaction. direction is "in" (money arriving) or "out" (money leaving)."""
    return {"date": START + timedelta(days=day), "customer": customer, "kind": kind,
            "direction": direction, "amount": round(amount, 2), "country": country}


def make_transactions(customers, rng):
    txs = []

    # Everyday activity for the normal customers: salary in, card spending and bills out.
    for cid, info in customers.items():
        if cid >= "C-101":
            continue
        monthly = info["expected_monthly"]
        for day in range(DAYS):
            if day % 30 == 0:
                txs.append(tx(day, cid, "salary", "in", monthly * rng.uniform(0.9, 1.1)))
            if rng.random() < 0.5:
                txs.append(tx(day, cid, "card", "out", rng.uniform(5, monthly / 25)))
            if rng.random() < 0.05:
                txs.append(tx(day, cid, "cash", "in", rng.uniform(50, monthly / 3)))
            if rng.random() < 0.03:
                txs.append(tx(day, cid, "wire", "out", rng.uniform(100, monthly / 2),
                              rng.choice(NORMAL_COUNTRIES)))

    # Innocent but unusual events. Real life is full of these, and they cause false alarms.
    # A café banks its weekly cash takings, which happen to be just under 10,000.
    cafe = next(cid for cid, info in customers.items() if info["job"] == "Café owner")
    for day in (10, 17, 24):
        txs.append(tx(day, cafe, "cash", "in", rng.uniform(8_700, 9_600)))
    # Someone receives an inheritance.
    txs.append(tx(33, "C-007", "transfer", "in", 60_000))
    # Someone moves their savings to another bank the day after selling their car.
    txs.append(tx(70, "C-015", "transfer", "in", 22_000))
    txs.append(tx(71, "C-015", "transfer", "out", 21_000))

    # C-101 Structuring: four cash deposits just under 10,000 in one week.
    for day, amount in [(40, 9_500), (42, 9_800), (44, 9_250), (46, 9_900)]:
        txs.append(tx(day, "C-101", "cash", "in", amount))

    # C-102 Pass-through (money mule): a big wire comes in, almost all of it leaves the next day.
    txs.append(tx(55, "C-102", "wire", "in", 48_000, "Spain"))
    txs.append(tx(56, "C-102", "wire", "out", 23_000, "USA"))
    txs.append(tx(56, "C-102", "wire", "out", 22_500, "France"))

    # C-103 High-risk country: payments to and from a high-risk jurisdiction.
    txs.append(tx(20, "C-103", "wire", "out", 18_000, "Ruritania"))
    txs.append(tx(63, "C-103", "wire", "in", 7_500, "Freedonia"))

    # C-104 Dormant account wakes up: nothing for months, then a large transfer.
    txs.append(tx(2, "C-104", "card", "out", 42))
    txs.append(tx(80, "C-104", "wire", "in", 35_000, "Ireland"))

    # C-105 Out of profile: a student with tens of thousands flowing through in one month.
    for day in range(30, 58, 4):
        txs.append(tx(day, "C-105", "transfer", "in", rng.uniform(3_000, 6_000)))

    txs.sort(key=lambda t: (t["date"], t["customer"]))
    return txs


# ---------------------------------------------------------------------------
# Step 2: the rules. Each one looks at the transactions and returns alerts.
# ---------------------------------------------------------------------------

def alert(customer, rule, reason, txs):
    return {"customer": customer, "rule": rule, "reason": reason,
            "date": max(t["date"] for t in txs), "amount": sum(t["amount"] for t in txs)}


def by_customer(txs):
    grouped = defaultdict(list)
    for t in txs:
        grouped[t["customer"]].append(t)
    return grouped


def rule_structuring(txs, customers):
    """Several cash deposits just under the reporting limit, close together."""
    limit = THRESHOLDS["cash_reporting_limit"]
    low = limit * THRESHOLDS["structuring_near_limit"]
    window = timedelta(days=THRESHOLDS["structuring_window_days"])
    alerts = []
    for cid, items in by_customer(txs).items():
        near = [t for t in items if t["kind"] == "cash" and t["direction"] == "in"
                and low <= t["amount"] < limit]
        for i, first in enumerate(near):
            group = [t for t in near[i:] if t["date"] - first["date"] <= window]
            if len(group) >= THRESHOLDS["structuring_min_count"]:
                alerts.append(alert(cid, "Structuring",
                                    f"{len(group)} cash deposits between {low:,.0f} and {limit:,} "
                                    f"within {window.days} days", group))
                break
    return alerts


def rule_pass_through(txs, customers):
    """A large amount arrives and most of it leaves again quickly."""
    window = timedelta(days=THRESHOLDS["pass_through_window_days"])
    alerts = []
    for cid, items in by_customer(txs).items():
        for t in items:
            if t["direction"] != "in" or t["amount"] < THRESHOLDS["pass_through_min_amount"]:
                continue
            outs = [o for o in items if o["direction"] == "out"
                    and t["date"] <= o["date"] <= t["date"] + window]
            out_total = sum(o["amount"] for o in outs)
            if out_total >= t["amount"] * THRESHOLDS["pass_through_out_share"]:
                alerts.append(alert(cid, "Rapid movement of funds",
                                    f"{t['amount']:,.0f} in, {out_total:,.0f} out "
                                    f"within {window.days} days", [t] + outs))
    return alerts


def rule_high_risk_country(txs, customers):
    """Any sizeable payment to or from a high-risk country."""
    return [alert(t["customer"], "High-risk country",
                  f"{t['amount']:,.0f} {t['direction']} with {t['country']}", [t])
            for t in txs
            if t["country"] in HIGH_RISK_COUNTRIES and t["amount"] >= THRESHOLDS["high_risk_min_amount"]]


def rule_dormant_account(txs, customers):
    """A large payment after a long quiet spell."""
    alerts = []
    for cid, items in by_customer(txs).items():
        for before, after in zip(items, items[1:]):
            gap = (after["date"] - before["date"]).days
            if gap >= THRESHOLDS["dormant_days"] and after["amount"] >= THRESHOLDS["dormant_wake_amount"]:
                alerts.append(alert(cid, "Dormant account reactivated",
                                    f"{after['amount']:,.0f} after {gap} quiet days", [after]))
    return alerts


def rule_out_of_profile(txs, customers):
    """A month's incoming money far above what the customer told the bank to expect."""
    alerts = []
    for cid, items in by_customer(txs).items():
        expected = customers[cid]["expected_monthly"]
        months = defaultdict(list)
        for t in items:
            if t["direction"] == "in":
                months[(t["date"] - START).days // 30].append(t)
        for month_txs in months.values():
            total = sum(t["amount"] for t in month_txs)
            if total >= expected * THRESHOLDS["out_of_profile_multiple"]:
                alerts.append(alert(cid, "Out of profile",
                                    f"{total:,.0f} in one month vs {expected:,} expected "
                                    f"({customers[cid]['job']})", month_txs))
    return alerts


RULES = [rule_structuring, rule_pass_through, rule_high_risk_country,
         rule_dormant_account, rule_out_of_profile]


# ---------------------------------------------------------------------------
# Step 3: run everything and show the results
# ---------------------------------------------------------------------------

def show_customer(cid, customers, txs):
    info = customers[cid]
    print(f"{cid}  {info['job']}, expects about {info['expected_monthly']:,} a month\n")
    for t in txs:
        if t["customer"] == cid:
            sign = "+" if t["direction"] == "in" else "-"
            print(f"  {t['date']}  {t['kind']:<8} {sign}{t['amount']:>10,.2f}  {t['country']}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--customer", help="show one customer's transactions, e.g. C-101")
    parser.add_argument("--csv", help="save the alerts to this CSV file")
    parser.add_argument("--seed", type=int, default=42, help="change this to get different random data")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    customers = make_customers(rng)
    txs = make_transactions(customers, rng)

    if args.customer:
        show_customer(args.customer, customers, txs)
        return

    alerts = [a for rule in RULES for a in rule(txs, customers)]
    alerts.sort(key=lambda a: (a["customer"], a["date"]))

    print(f"Checked {len(txs):,} transactions for {len(customers)} customers "
          f"with {len(RULES)} rules.\n")
    print(f"{len(alerts)} alerts:\n")
    for a in alerts:
        print(f"  {a['customer']}  {a['date']}  {a['rule']:<28} {a['reason']}")

    planted = {"C-101", "C-102", "C-103", "C-104", "C-105"}
    alerted = {a["customer"] for a in alerts}
    print(f"\nPlanted suspicious customers caught: {len(planted & alerted)} of {len(planted)}")
    missed = planted - alerted
    if missed:
        print(f"Missed: {', '.join(sorted(missed))}")
    false_alarms = [a for a in alerts if a["customer"] not in planted]
    print(f"False alarms (alerts on ordinary customers): {len(false_alarms)}")

    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["customer", "date", "rule", "reason", "amount"])
            writer.writeheader()
            writer.writerows(alerts)
        print(f"\nSaved alerts to {args.csv}")


if __name__ == "__main__":
    main()
