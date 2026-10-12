# Running the psychologist evaluation (30 testers)

## Goal
Collect structured, honest feedback from practising psychologists and counsellors on whether Manas Twin's
early-warning signal, explanations and workflow would be useful, trustworthy and safe. This is a usability and
face-validity study of a prototype on synthetic clients, not a clinical trial.

## Before the session
1. Start the app: `python -m streamlit run app/streamlit_app.py` (or `docker compose up`).
2. Open it in a browser, full screen, light mode (switch to dark only on request).
3. Click **🔄 New tester · reset the app** in the sidebar before each tester.
4. Keep this one-liner ready: *"This is a research prototype on computer-generated clients. It predicts whether a
   depressive episode is likely to start in the next 7 days and is meant as a prompt for a human check-in, never a
   diagnosis. Please be as critical as you like."*

## Session plan (≈15 minutes per tester)
| Time | Step |
|---|---|
| 0–3 min | Tester reads **📘 Guide** (you can summarise aloud) |
| 3–13 min | Tester works through the 5 guided tasks (Story → Twin → Clinician → What-if → Evidence). Do not steer; note where they hesitate or misread something |
| 13–15 min | Tester fills **📝 Feedback** |

Observation prompts for you (write down verbatim quotes when possible):
- Where did they pause or look confused? Which words did they ask about?
- At what day did *they* say they would have been concerned about Arjun, vs. day 110 when the twin flagged?
- Did they read the what-if caveat? Did they treat the estimate as causal?
- What did they say unprompted about false alarms, consent, or crisis handling?

## Where the data goes
- Answers are appended to `feedback/responses.csv` on the demo machine (no client data, no health data).
- Organiser view: **📝 Feedback → 🔐 Organiser tools**, passcode `manas2026` (change it by setting the environment
  variable `MANAS_ADMIN_CODE`). Shows the response count, mean rating per statement and a CSV download.
- Back the CSV up after every few testers.
- Remote testers (cloud link): set up the Google Sheets sync (`docs/GOOGLE_SHEETS_SYNC.md`) so every response lands in a sheet you own; the organiser view then reads from the sheet.

## Analysing the results
- Report n, role mix, and the mean ± SD for each of the 10 statements (1–5).
- Flag any statement with a mean below 3.5 as a redesign priority.
- Code the open answers into themes (trust, missing features, ethics, workflow). Quote 3–5 representative lines.
- Put a one-slide summary in the deck: "What 30 psychologists told us, and what we changed."

## Consent and ethics for the session
- Explain that feedback is stored locally, anonymised by default (name and email optional).
- No real client cases should be entered anywhere in the app; the **Enrol a demo client** feature creates a
  synthetic person only.
- If a tester raises a personal mental-health concern, pause the session and share the Tele-MANAS number (14416).
