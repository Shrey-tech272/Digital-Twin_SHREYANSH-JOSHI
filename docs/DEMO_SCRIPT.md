# Demo Video Script (target: 17 minutes)

**Setup before recording**
- Run `streamlit run app/streamlit_app.py`, browser zoom 90%, close other tabs.
- Have the presentation PDF open in another window.
- Record with OBS / Loom / Zoom (screen + webcam bubble). Speak slowly. It's fine to pause and cut later.
- Upload to YouTube as **Unlisted** (not Private), then paste the link into the README.

---

## 0:00 – 1:30 · Hook and problem (slides 1–3)
> "Depression rarely arrives overnight. In the weeks before an episode, sleep changes, bedtime drifts, heart-rate variability falls, people move less and withdraw. Nobody is watching those signals, so care starts late, if at all. India's National Mental Health Survey found nearly 15% of adults need mental-health care and the treatment gap is above 60% for almost every disorder."

> "We built **Manas Twin**: a digital twin of one person's mind-body rhythm that warns about a week *before* a depressive episode is likely to begin."

## 1:30 – 3:00 · Why a digital twin (slides 4–5)
- Everyone's normal is different: 6 hours of sleep is fine for one person, a red flag for another.
- The twin learns *your* normal from your wearable, pairs it with your health record, and does four things: **mirror, predict, explain, simulate**.
- Users: students and young professionals; counsellors, campus wellness centres, corporate EAPs and doctors.

## 3:00 – 4:30 · Architecture (architecture PDF)
Walk left to right: data sources (wearable, phone, EHR / PHQ-9, calendar) → consent and privacy layer (DPDP Act, ABDM consent, pseudonymisation, FHIR) → twin core (personal baseline engine, drift index, XGBoost risk engine, SHAP explainer, what-if simulator) → interfaces (person, clinician, alert pathway to Tele-MANAS) → feedback loop for retraining.
Say clearly which parts are built in this PoC and which are roadmap.

## 4:30 – 5:30 · Data honesty (slide on data)
> "No public dataset links daily wearables to health records for Indian young adults, so we built a simulator of 600 synthetic people over 240 days, following patterns from the digital-phenotyping literature. Everything you'll see is synthetic, and the ground-truth episodes are hidden from the model and only used to evaluate it."
Show `src/simulator.py` briefly (scroll the docstring).

## 5:30 – 9:30 · Live demo: 📖 Story mode (the app opens here)
Click **Next →** through the six steps and read each card in your own words:
1. **Meet Arjun** (6 Apr): point at ☀️ *Clear skies* and the body-rhythm cards. "The shaded band on each card is *his* normal."
2. **Exams begin** (19 Apr): ⛅ *Clouds gathering*. "Small changes a population rule would ignore, but big for *him*."
3. **Early warning, 7 days ahead** (21 Apr): ⛈️ *Storm likely*. Read the plain-English summary, then the "Why the twin is worried" list.
4. **The episode begins** (28 Apr): the grey band appears. "Exactly the window the twin warned about."
5. **Usual care catches up, 19 days late** (17 May): "🩺 diagnosed" marker. "Support could have started 26 days earlier."
6. **What if he'd had a better week?** Storm (6.4%) → Clear skies (0.7%). Read the caveat aloud.

Tip: flip **🌙 Dark mode** once during the demo; it shows polish.

## 9:30 – 12:00 · 🧠 Twin and 🔮 What-if (hands-on)
1. **🧠 Twin** tab, person ⭐ Arjun: drag the sidebar date from **day 105 to 125** and narrate the weather changing.
2. Explain the three blocks: mind-weather headline, outlook chart (green / amber / red zones), body-rhythm cards.
3. **🔮 What-if** tab: click **😴 Sleep more**, then **🌿 Full healthy week**, then move one slider yourself. Point out "falls by 89%" and what would still push risk up.

## 12:00 – 13:30 · Clinician panel
1. Show the risk-ranked caseload for the chosen day: number of early warnings and watch cases.
2. Show the EHR timeline and PHQ-9 trend chart with severity bands.
3. Expand **FHIR bundle**: "This is how the twin would exchange data in India's ABDM ecosystem: ICD-10, LOINC, ATC codes."

## 13:30 – 14:30 · Live feed
Pick MT0156 (IT professional), start at about day 70, 20 days, *normal* speed, click **Start live replay**. Narrate while the risk line grows and the banner turns from green to amber to red.

## 14:30 – 16:00 · Model performance
- Patient-level split: 420 train / 180 never-seen test people.
- Twin vs population model: AUROC 0.85 vs 0.81; 48% vs 40% of episodes flagged in advance; median 6-day lead; ~25% fewer false-alert days.
- Be upfront: "About half of episodes are caught early. That's why it's a prompt for a human check-in, not a diagnosis."

## 16:00 – 17:00 · Responsible AI, roadmap, close (final slides)
- Consent-first (DPDP Act 2023), human in the loop, explanations for every alert, **no suicide-risk prediction**, Tele-MANAS 14416 signposting.
- Roadmap: DEPRESJON validation (loader built), university wellness-centre pilot, Health Connect / HealthKit ingestion, ABDM integration.
> "Medicine that is proactive, not reactive, starts with knowing what normal looks like for each of us. Thank you."
