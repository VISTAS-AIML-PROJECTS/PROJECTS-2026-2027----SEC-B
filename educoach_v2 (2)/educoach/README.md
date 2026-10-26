# EduCoach AI (v2)

Adaptive placement-preparation platform built with Flask, SQLite and scikit-learn.

## Run (Windows)
1. Install Python 3.11 or newer.
2. In PowerShell, inside this folder:
   `py -3.11 -m venv venv` then `venv\Scripts\activate`
3. `python -m pip install -r requirements.txt`
4. `python app.py` and open http://127.0.0.1:5000

The database is created and seeded automatically in `data/`. The **first account you register becomes admin**
(or set the `ADMIN_EMAIL` environment variable). Run the tests with `python -m unittest discover -s tests -v`.

## What changed from v1
| Area | v1 | v2 |
|---|---|---|
| Questions | 1 question repeated 90x per topic | 370+ distinct questions; aptitude questions are generated with correct answers and worked explanations; CSV import for more |
| Adaptivity | last score picks Easy/Medium/Hard | Elo-style ability rating per topic; questions are chosen near your rating and recently seen ones are avoided |
| Analytics | per-test score only | per-question accuracy per topic, even in mixed tests; weak/strong topics need 3+ answers |
| ML model | random synthetic data, label = score threshold | simulated cohort with noisy hidden skill; reports hold-out accuracy, CV, confusion matrix, importances (page: Model) |
| Tests | no timer, no review | every test has exactly 30 questions (change `TEST_QUESTIONS` in app.py; never above 30), countdown timer with auto-submit, full answer review with explanations, mistake notebook |
| Coding | code was only stored | 13 problems with hidden test cases; Python is auto-judged (Accepted / Wrong Answer / Runtime Error / Time Limit) |
| Mentor | templated sentences | trend detection, ability levels, weak/strong topics, personalised 7-day plan |
| Security | unsalted SHA-256, hard-coded secret, no CSRF, debug on | salted password hashes, generated secret key, CSRF tokens, login throttling, password rules, POST logout, admin role |
| Admin | none | question stats and CSV import |
| Quality | none | 22 automated tests |

## Project layout
`app.py` routes, adaptive engine and analytics | `bank.py` question builder and aptitude generators | `catalog.py` topics |
`extra_questions.py` curated questions | `ml.py` readiness model | `judge.py` + `problems.py` coding judge | `templates/`, `static/` UI | `tests/`

## Honest limitations (say these in your viva)
- **The ML model is trained on a simulated cohort**, because no real placement-outcome data exists. It demonstrates the pipeline
  (features, training, evaluation) but is not a validated predictor. Replace `simulate_cohort` with real labelled data when you have it.
- **The code judge is not a full sandbox.** It runs Python in a separate process with timeout and (on Linux/macOS) memory limits.
  Do not expose it to the public internet without running it inside a container. Set `JUDGE_TIME_LIMIT` / `JUDGE_MEMORY_MB` to tune.
- Many technical topics still have only 1-3 questions. Each test is filled to 30 questions from the topic first, then the rest of the subject, then the rest of the category (the test page says so).
  Grow the bank through Admin > Import CSV (template included in `data/questions_template.csv`).
- Only Python submissions are auto-judged; other languages are saved.

## Suggested next steps
Real placement data for the model, more questions per topic, a Docker-based multi-language judge, email verification and password reset.
