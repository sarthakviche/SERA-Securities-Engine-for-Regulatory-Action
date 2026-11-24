# SERA — Market Research & Hackathon Strategy

_Researched 2026-11-24. Market figures come from analyst summaries and vary widely, so treat them as ranges._

## 1. Market context
- **India RegTech is growing fast but the sizing is uncertain.** Estimates for 2025–26 range from roughly USD 0.3 bn to 0.73 bn, with CAGRs of 16–36% to the early 2030s ([IMARC](https://www.imarcgroup.com/india-regtech-market), [MRFR](https://www.marketresearchfuture.com/reports/india-regulatory-technology-market-61713), [BlueWeave](https://www.blueweaveconsulting.com/report/india-regtech-market/report-sample)). Ken Research sizes the broader RegTech plus compliance-SaaS segment at about USD 1.5 bn ([Ken Research](https://www.marketresearch.com/Ken-Research-v3771/India-RegTech-Compliance-SaaS-44316942)).
- **SEBI itself is asking for this.** The *Securities Market TechSprint* at GFF '26 lists **"Agentic Compliance"** as a problem statement: agentic AI that bridges complex regulatory text and on-ground compliance action ([GFF SEBI TechSprint](https://www.globalfintechfest.com/gff-hackathons/sebi-techsprint), [Outlook Business](https://www.outlookbusiness.com/markets/sebi-launches-securities-market-hackathon)). SERA *is* that problem statement.
- **Incumbents and competitors:**
  - MetricStream (AI obligation extraction, traceable to source), [MetricStream](https://www.metricstream.com/blog/ai-powered-obligation-extraction-regulatory-review.html)
  - AscentAI ("obligations as the unit of regulatory change"), [FinTech Global](https://fintech.global/2026/10/30/why-ascentai-makes-obligations-the-unit-of-regtech-change/)
  - Compliance.ai (impact on specific firms), [WatersTechnology](https://www.waterstechnology.com/regulation-compliance/3965146/complianceai-releases-automated-regulatory-change-workflow-platform)
  - Harvey (interpretation-first compliance AI), [Harvey](https://www.harvey.ai/blog/ai-for-regulatory-compliance)
  - Vixio (AI extraction plus expert validation), [Vixio](https://www.vixio.com/blog/tools-that-use-ai-to-analyse-regulatory-documents-and-highlight-compliance-obligations)
  - All of these are global and enterprise-priced, and none is SEBI-native or built for the long tail of ~1,000s of Indian brokers, DPs, IAs and RAs.
- **The industry's pain point is interpretation and trust, not monitoring.** Vendors frame interpretation as the hard part. Surveys cited in 2026 show high adoption intent but a majority rating AI risk as high. **Judges will ask "how do I trust it?"**

## 2. Positioning
> **SERA is the SEBI-native agentic compliance engine for mid-size intermediaries: it turns every circular into cited obligations, owner-assigned tasks and regulator-ready evidence, and it runs fully on-prem.**

| Judge question | SERA's answer (built and demoable) |
|---|---|
| "Does the AI hallucinate?" | Every obligation quotes its **verbatim source sentence + paragraph + page**. When an LLM is used, its proposals are **discarded unless the quote is found in the PDF** (the hallucination guard is unit-tested). |
| "Who is accountable?" | **Two human gates**: Gate 1 for interpretation, Gate 2 for the SOPs and plan. Agents draft and humans approve, which fits SEBI's "agentic + human oversight" framing. |
| "Can a regulator trust the records?" | **SHA-256 hash-chained audit trail** with a live **Verify** button. `scripts/tamper_demo.py` edits a row in Postgres and the chain shows as broken. |
| "Our data can't leave the building." | **Runs fully offline** (local Postgres plus a deterministic engine, no API keys). An LLM is optional and only used for proposals. This fits data-residency expectations under SEBI's cybersecurity framework. |
| "Is this only a demo?" | Real SEBI PDFs, a real scraper, a real DB, file-hashed evidence, compliance roll-up and CSV export, plus 10 engine tests and an E2E smoke script. |
| "What about scanned circulars?" | **Fail-closed.** SERA refuses to guess when there is no text layer. OCR is the next step. |

## 3. Differentiators implemented this session
1. Citation-verified obligation extraction (clause, page and verbatim quote) with a confidence score.
2. Applicability against the **org profile** (16 SEBI intermediary types), with the reason stated in plain English.
3. Ambiguity detector (undefined standards, deferred specifications, conditional applicability, event-relative deadlines) that raises interpretation questions.
4. Deadline intelligence: explicit dates, extensions applied to the obligations they modify, effective dates, and **event-driven SLAs** (e.g. "within 7 working days of closure") kept apart from one-off deadlines.
5. Impact map (departments with roles, systems), with **fail-closed human review** for unmapped departments.
6. SOP amendment drafts and a 3-phase plan (Assess → Implement → Validate). Gate 2 feedback becomes tracked tasks.
7. Evidence vault: uploads are SHA-256 fingerprinted, chained into the audit log, and task completion rolls up to obligation and circular compliance.
8. Live compliance-health dashboard, risk heat counts and upcoming deadlines.
9. One-click local launcher (Postgres, migrations, API and UI).

## 4. Pitch outline (3 minutes)
1. **Problem (20s):** SEBI issued hundreds of circulars this year. A mid-size broker's 3-person compliance team reads PDFs, emails department heads and tracks it all in Excel. Missed deadlines mean penalties.
2. **Live demo (2 min):** follow `04_DEMO_SCRIPT.md`.
3. **Why we win (30s):** cited and verifiable, human-gated, tamper-evident, on-prem, and SEBI-native.
4. **Business (10s):** per-entity SaaS or on-prem licence for brokers, DPs, IAs and RAs. Later: exchange/ANMI partnerships, RBI/IRDAI packs.

## 5. Roadmap after the hackathon
- OCR for scanned circulars (RapidOCR/Tesseract, fully local).
- Cross-circular "change analysis" against Master Circulars, with a clause diff.
- Recurring obligations becoming a scheduled compliance calendar (the backend has recurrence fields).
- Multi-user auth and RBAC (department heads approve only their own tasks).
- Scheduled SEBI monitoring (replace the empty Celery stubs with an APScheduler job).
- Additional regulators: RBI, IRDAI, MCA.
