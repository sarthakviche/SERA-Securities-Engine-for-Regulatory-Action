# SERA — Live Demo Script (about 4 minutes)

**Before you start:** run `backend\.venv\Scripts\python.exe backend\scripts\reset_demo.py` for a clean slate, then double-click **Start SERA**.

| # | Screen | Do | Say |
|---|---|---|---|
| 1 | Dashboard | Show the empty pipeline and "Set up organisation" | "SERA runs fully on this laptop: Postgres, API and UI. No data leaves." |
| 2 | Onboarding | Tick *Stock Broker, Depository Participant, IA, RA*. Save. | "Applicability is decided against who **we** are." |
| 3 | Inbox | Show the real SEBI circulars. Click **Analyse** on *"Ease of doing business… Stock Brokers"*. Also try **Sync from SEBI** or drag in any PDF. | "Scraped from sebi.gov.in or uploaded." |
| 4 | Workspace | Hover an obligation and the source paragraph lights up. Point at the verbatim quote, Para/page, applicability reason and the ambiguity flag on "appropriately tagged". | "Every obligation is cited. If an LLM proposes something it can't quote from the PDF, SERA throws it away." |
| 5 | Workspace | Untick one item (it becomes waived, with the decision on record) and click **Approve interpretation** (Gate 1). | "Agents draft, humans decide." |
| 6 | Impact Map | Department load, systems touched, owner/contributor roles. | "Unmatched departments go to human review. It doesn't guess." |
| 7 | Plan | SOP amendments tab, then **Request changes**: "Add a UAT step for IT". | "The reviewer's feedback becomes a tracked task." Then **Approve plan** (Gate 2). |
| 8 | Tracker | Start a task, then **Submit evidence** and attach any file. | "Evidence is SHA-256 fingerprinted." |
| 9 | Audit Trail | Click **Verify chain integrity**: green. Run `scripts\tamper_demo.py` and verify again: red, "chain broken at #N". Then run `--undo`. | "Even a DB admin can't quietly rewrite who approved what." |
| 10 | Register / Dashboard | Export CSV, show the health score moving. | "Regulator-ready in one click." |

**Bonus:** the PaRRVA circular shows deadline intelligence. Para 3 extends the Para 2 deadline, and SERA applies the extension to the obligation automatically.
