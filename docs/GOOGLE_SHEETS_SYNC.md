# Google Sheets sync for tester feedback (10-minute setup)

Every feedback submission is always saved to `feedback/responses.csv` on the machine running the app.
When the app runs in the cloud (Streamlit Community Cloud), that file is temporary, so this sync pushes each
response to a Google Sheet you own as well. The organiser view then reads from the sheet.

## 1. Create the sheet and the script
1. Create a new Google Sheet (any name, e.g. *Manas Twin feedback*).
2. Open **Extensions → Apps Script**. Delete the sample code and paste the contents of
   `docs/google_sheets_sync/Code.gs`.
3. Change `SECRET_KEY` to a private string (letters and numbers, e.g. `mt-feedback-7Qp2x`). Save (Ctrl+S).

## 2. Deploy it as a web app
1. Click **Deploy → New deployment**.
2. Click the gear next to "Select type" and choose **Web app**.
3. Settings: Description *Manas Twin feedback* · **Execute as: Me** · **Who has access: Anyone**.
4. Click **Deploy**, approve the permissions (Google will warn that the app is unverified; click *Advanced → Go to … (unsafe)* — it is your own script).
5. Copy the **Web app URL** (it looks like `https://script.google.com/macros/s/AKfy…/exec`).

If you later change the script, you must **Deploy → Manage deployments → Edit → New version** for the change to go live.

## 3. Give the app the URL and key
**Streamlit Community Cloud:** in the app's **Settings → Secrets**, paste:
```toml
FEEDBACK_WEBHOOK_URL = "https://script.google.com/macros/s/AKfy.../exec"
FEEDBACK_WEBHOOK_KEY = "mt-feedback-7Qp2x"
MANAS_ADMIN_CODE = "your-private-organiser-passcode"
```
**Running locally:** create `.streamlit/secrets.toml` with the same three lines (this file is git-ignored).
You can also set them as environment variables with the same names.

## 4. Test it
1. Restart the app, open **📝 Feedback**, submit a test response.
2. You should see "…has also been synced to the research team's sheet", and a new row in the sheet
   (a header row is created automatically on the first submission).
3. In **🔐 Organiser tools** the status should read *Google Sheets sync: on*.

If the sync fails, the response is still saved locally and the tester sees a gentle note; nothing is lost.

## Privacy
The sheet contains testers' ratings and comments, plus name and email only if they chose to give them.
It contains no client data. Keep the sheet private and do not share the web app URL or key publicly.
