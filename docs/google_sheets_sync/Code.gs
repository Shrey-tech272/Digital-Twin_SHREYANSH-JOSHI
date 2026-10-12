/**
 * Manas Twin - feedback sync endpoint (Google Apps Script)
 *
 * Paste this into Extensions -> Apps Script of the Google Sheet that should receive the feedback.
 * Set SECRET_KEY to a private string, then Deploy -> New deployment -> Web app
 *   Execute as: Me   |   Who has access: Anyone
 * Copy the Web app URL into the app's secrets as FEEDBACK_WEBHOOK_URL and the key as FEEDBACK_WEBHOOK_KEY.
 */
const SHEET_NAME = "responses";
const SECRET_KEY = "change-me-to-something-private";

function json(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}

function getSheet() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  return ss.getSheetByName(SHEET_NAME) || ss.insertSheet(SHEET_NAME);
}

// Receives one feedback response as JSON and appends it as a row.
function doPost(e) {
  const lock = LockService.getScriptLock();
  lock.tryLock(10000);
  try {
    const data = JSON.parse(e.postData.contents || "{}");
    if (data.key !== SECRET_KEY) return json({ ok: false, error: "bad key" });
    delete data.key;
    const sh = getSheet();
    if (sh.getLastRow() === 0) sh.appendRow(Object.keys(data));
    const headers = sh.getRange(1, 1, 1, sh.getLastColumn()).getValues()[0];
    sh.appendRow(headers.map(h => (data[h] === undefined ? "" : data[h])));
    return json({ ok: true });
  } catch (err) {
    return json({ ok: false, error: String(err) });
  } finally {
    lock.releaseLock();
  }
}

// Returns all responses as JSON (used by the organiser view). Requires ?key=...
function doGet(e) {
  if (!e || !e.parameter || e.parameter.key !== SECRET_KEY) return json({ ok: false, error: "bad key" });
  const sh = getSheet();
  if (sh.getLastRow() === 0) return json([]);
  const values = sh.getDataRange().getValues();
  const headers = values.shift();
  return json(values.map(r => Object.fromEntries(headers.map((h, i) => [h, r[i]]))));
}
