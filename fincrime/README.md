# Financial crimes alerting demo

A small, self-contained demo of how a bank's anti-money-laundering (AML) alerting works.
Everything is made up. It needs only Python 3, with no extra installs.

```
python3 alerting_demo.py                   run the rules and show the alerts
python3 alerting_demo.py --customer C-101  show one customer's transactions
python3 alerting_demo.py --csv alerts.csv  also save the alerts to a spreadsheet
python3 alerting_demo.py --seed 7          different random data
```

## What it does

1. **Makes up data.** 90 days of transactions for 45 customers: salaries, card spending,
   cash deposits and wires. Each customer has a job and the monthly amount they told the
   bank to expect.
2. **Hides five suspicious customers** among them (C-101 to C-105), plus a few ordinary
   people doing unusual but innocent things, such as an inheritance or a café banking its takings.
3. **Runs five rules** and prints the alerts:

| Rule | Looks for | Planted case |
|---|---|---|
| Structuring | Several cash deposits just under the 10,000 reporting limit | C-101, a taxi driver |
| Rapid movement of funds | Big amount in, most of it out again within days (a "money mule") | C-102 |
| High-risk country | Payments with high-risk countries (fictional names here) | C-103 |
| Dormant account reactivated | Months of silence, then a large payment | C-104 |
| Out of profile | A month's income far above what the customer said to expect | C-105, a student |

4. **Scores itself.** It counts how many planted customers were caught and how many alerts
   were false alarms on ordinary customers.

## Things to try

- **Tuning.** Change `structuring_window_days` from 7 to 14 in `THRESHOLDS`. The café owner,
  who banks takings weekly, starts getting flagged. You catch more, but you also annoy more
  innocent people and give analysts more to review. Picking thresholds is a constant trade-off.
- Set `out_of_profile_multiple` to 3 or 10 and watch the false alarms go up or down.
- Look at a false alarm (`--customer C-007`) and ask what extra information an analyst would
  need to close it. This is what Level 1 triage does.
- Add your own rule: write a function like the others and add it to `RULES`.
