# KBC Time Machine — Project Info

## Open questions
- **Platform?** → Simple web app, shown on a laptop / projector (decided 2026-09-30).

## Key discoveries
- **Synthetic data** (`sim-user-data.json`) is produced by `generate_sim_user_data.py`, which is deterministic because it uses a fixed seed. To change the data, edit the script and run `python3 generate_sim_user_data.py`; don't hand-edit the JSON. It holds 24 months (Oct 2024 – Sep 2026) of transactions, a monthly summary and recurring payments for each profile.
- Demo scenarios planted in the data: **BE002 (De Smet)** has a grocery spike in Sep 2026 (€1,420 against a usual ~€900–1,000) and ends the month with only €935 on the current account. **BE001 (Jean)** finishes paying off his car loan in Feb 2026, after which his monthly saving goes €200 → €300 → €450.
- Judging (Tectonic Hackathon): Creativity, Technical ability ("does it work?"), Fit, Security.
- "Secure" is defined by an **Aikido AI Code Audit** run on the public GitHub repo (10% of the score). It looks for business-logic flaws, IDOR, authentication and authorization weaknesses. You submit before/after screenshots, and the score is based on the issues that remain.
- The KBC challenge asks for a *scalable personalization approach* (2.3M customers), not "just another feature".
- Submission needs a public GitHub repo, a README (what it is, how to run it, what's unfinished), a demo video under 3 minutes and the Aikido screenshots. No secrets in the repo.

## Known gotchas
- The data contains internal transfers, which appear as two legs sharing a `transfer_id`, and credit-card repayments. Neither counts as income or spending. Card purchases sit on the `-CC` account and must be counted once. `monthly_summary` already applies these rules.
- The folder is not a git repo yet, but Aikido needs a connected GitHub repo.
