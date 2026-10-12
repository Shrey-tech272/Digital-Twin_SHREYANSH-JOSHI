# Submission Checklist

| # | Requirement | Where it is | Your action |
|---|---|---|---|
| 1 | Project Title | `README.md` heading | Done |
| 2 | Problem Statement | `README.md` section 1 | Done |
| 3 | Healthcare Use Case | `README.md` section 2 | Done |
| 4 | Technical Stack | `README.md` section 4 | Done |
| 5 | AI/ML Model or Framework Details | `README.md` section 5 + `MODEL.md` | Done |
| 6 | 15–20 min demo video, unlisted YouTube, link in README | `docs/DEMO_SCRIPT.md` | **Record, upload as Unlisted, replace `REPLACE_WITH_YOUR_LINK` in README** |
| 7 | Open-source License Details | `LICENSE` (MIT) + README section 12 | Put your team name in `LICENSE` line 3 |
| 8 | Architecture Diagram in PDF/PPT | `docs/Manas_Twin_Architecture.pdf` / `.pptx` | Done |
| 9 | Presentation in PDF/PPT | `docs/Manas_Twin_Presentation.pdf` / `.pptx` | Add team names on the title slide |
| 10 | All files and links publicly accessible | - | See checks below |

## Public-access checks (do these last)
- [ ] GitHub repo visibility is **Public** (Settings → General → Danger Zone → Change visibility).
- [ ] YouTube video is **Unlisted**, not Private. Test the link in an incognito window.
- [ ] Open the repo in an incognito window: README renders, PDFs open, images show.
- [ ] No Google Drive links needing access requests (everything lives inside the repo).
- [ ] Team table filled in README section 11.

## Uploading to GitHub (first time)
```bash
cd manas-twin
git init
git add .
git commit -m "Manas Twin: digital twin PoC for depressive-episode early warning"
git branch -M main
git remote add origin https://github.com/<your-username>/manas-twin.git
git push -u origin main
```
(Create the empty repo `manas-twin` on github.com first, without a README, so the push doesn't conflict.)
