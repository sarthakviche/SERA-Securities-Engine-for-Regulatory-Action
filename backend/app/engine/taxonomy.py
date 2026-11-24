"""Domain vocabulary for Indian securities-market regulation (SEBI-first)."""
from __future__ import annotations

import re

ENTITY_PATTERNS: dict[str, list[str]] = {
    "stock_broker": [r"stock ?brokers?", r"\bbrokers?\b", r"trading members?"],
    "depository_participant": [r"depository participants?", r"\bDPs?\b"],
    "depository": [r"\bdepositor(?:y|ies)\b(?! participant)"],
    "stock_exchange": [r"stock exchanges?", r"\bexchanges?\b"],
    "investment_adviser": [r"investment advis[eo]rs?", r"\bIAs?\b"],
    "research_analyst": [r"research analysts?", r"\bRAs?\b"],
    "mutual_fund": [r"mutual funds?", r"asset management compan(?:y|ies)", r"\bAMCs?\b"],
    "portfolio_manager": [r"portfolio managers?"],
    "aif": [r"alternative investment funds?", r"\bAIFs?\b"],
    "listed_entity": [r"listed (?:entit(?:y|ies)|compan(?:y|ies))"],
    "rta": [r"registrars? to an issue", r"share transfer agents?", r"\bRTAs?\b"],
    "kra": [r"KYC registration agenc(?:y|ies)", r"\bKRAs?\b"],
    "clearing_corporation": [r"clearing corporations?"],
    "merchant_banker": [r"merchant bankers?"],
    "credit_rating_agency": [r"credit rating agenc(?:y|ies)"],
    "bank": [r"\bbanks?\b"],
}

ENTITY_LABELS: dict[str, str] = {
    "stock_broker": "Stock Broker",
    "depository_participant": "Depository Participant",
    "depository": "Depository",
    "stock_exchange": "Stock Exchange",
    "investment_adviser": "Investment Adviser",
    "research_analyst": "Research Analyst",
    "mutual_fund": "Mutual Fund / AMC",
    "portfolio_manager": "Portfolio Manager",
    "aif": "Alternative Investment Fund",
    "listed_entity": "Listed Entity",
    "rta": "Registrar & Transfer Agent",
    "kra": "KYC Registration Agency",
    "clearing_corporation": "Clearing Corporation",
    "merchant_banker": "Merchant Banker",
    "credit_rating_agency": "Credit Rating Agency",
    "bank": "Bank",
}

# entity types that an org can register as (bank is only a qualifier)
SELECTABLE_ENTITIES = [k for k in ENTITY_LABELS if k != "bank"]

DEFAULT_DEPARTMENTS = [
    "Compliance",
    "Legal",
    "Operations",
    "IT & Information Security",
    "Client Servicing",
    "Finance & Accounts",
    "Research & Advisory",
    "Marketing",
    "Risk Management",
    "Internal Audit",
]

DEFAULT_SYSTEMS = [
    "Back-office (BOS)",
    "Exchange Reporting Portal",
    "CRM & Client Communication",
    "KYC / Onboarding System",
    "Website & Marketing Collateral",
    "Document Management System",
    "Policy & SOP Repository",
    "Trading Platform",
]

CATEGORY_RULES: list[tuple[str, str]] = [
    ("Cybersecurity", r"cyber|security|vapt|\bsoc\b|incident|breach"),
    ("Registration & Enrolment", r"enrol|registration|register with|empanel"),
    ("Account Operations", r"demat|bank account|nomenclature|tagg?ed|tagging|naming"),
    ("Reporting & Disclosure", r"\breport|inform|communicat|submit|disclos|\bfile\b|intimat"),
    ("Record Keeping", r"maintain records|retain|preserv|record"),
    ("Client Protection", r"client|investor|\bkyc\b|mobile|grievance|nominee"),
    ("Governance", r"bye-?laws|rules and regulations|board|policy|amendment"),
    ("Timeline / Effective Date", r"extend|timeline|come into force|effect from"),
]

CATEGORY_WEIGHT = {
    "Cybersecurity": 3,
    "Client Protection": 2,
    "Reporting & Disclosure": 2,
    "Registration & Enrolment": 2,
    "Account Operations": 1,
    "Record Keeping": 1,
    "Governance": 1,
    "Timeline / Effective Date": 1,
    "General Compliance": 1,
    "Exemption": 0,
}

EVIDENCE_BY_CATEGORY = {
    "Cybersecurity": "Audit/VAPT report and remediation sign-off by CISO",
    "Registration & Enrolment": "Enrolment / registration confirmation issued by the agency",
    "Account Operations": "Updated list of bank & demat accounts showing the prescribed nomenclature",
    "Reporting & Disclosure": "Submission acknowledgement / portal receipt with timestamp",
    "Record Keeping": "Records extract and approved retention policy",
    "Client Protection": "Sample client records / communication logs demonstrating compliance",
    "Governance": "Board / committee approved policy or amended bye-laws",
    "Timeline / Effective Date": "Updated compliance calendar entry approved by Compliance Officer",
    "General Compliance": "Compliance Officer sign-off memo",
    "Exemption": "Documented exemption assessment approved by Compliance Officer",
}

DEPT_RULES: list[tuple[str, list[str]]] = [
    (r"cyber|security|system|software|portal|technolog|digital|website|accessib", ["IT & Information Security"]),
    (r"demat|bank account|nomenclature|tagg?ed|tagging", ["Operations", "Finance & Accounts"]),
    (r"client|investor|customer|mobile|\bkyc\b|grievance", ["Client Servicing", "Operations"]),
    (r"enrol|registration|register", ["Compliance", "Legal"]),
    (r"performance data|research|recommendation|advice|advis", ["Research & Advisory", "Marketing"]),
    (r"\breport|inform|communicat|submit|intimat", ["Compliance", "Operations"]),
    (r"bye-?laws|rules and regulations|policy|board", ["Legal", "Compliance"]),
    (r"record|retain|preserv|audit", ["Compliance", "Internal Audit"]),
    (r"risk|margin|exposure", ["Risk Management"]),
]

SYSTEM_RULES: list[tuple[str, str]] = [
    (r"demat|bank account|nomenclature|tag", "Back-office (BOS)"),
    (r"(report|inform|communicat|submit)\w*[^.]{0,60}(stock )?exchange|exchange[^.]{0,40}(report|inform)", "Exchange Reporting Portal"),
    (r"client|investor|communicat", "CRM & Client Communication"),
    (r"\bkyc\b|mobile|onboard|verification", "KYC / Onboarding System"),
    (r"performance data|website|advertis|marketing|accessib", "Website & Marketing Collateral"),
    (r"record|retain|preserv", "Document Management System"),
    (r"bye-?laws|policy|procedure|sop", "Policy & SOP Repository"),
    (r"trading|order|algo", "Trading Platform"),
]

AMBIGUITY_TERMS: list[tuple[str, str, str]] = [
    (r"\bappropriate(ly)?\b", "Undefined standard",
     "'Appropriate' is not defined - the expected standard of compliance must be interpreted."),
    (r"\breasonable\b", "Undefined standard", "'Reasonable' leaves the standard to interpretation."),
    (r"\badequate\b|\bsufficient\b|\bsuitable\b", "Undefined standard",
     "Qualitative threshold without objective criteria."),
    (r"as may be (specified|prescribed|notified)", "Deferred specification",
     "Details are deferred to a future specification that is not yet available."),
    (r"from time to time", "Open-ended scope", "Requirement may change without a fixed review cycle."),
    (r"as the case may be|as applicable|where applicable|wherever applicable", "Unclear scope",
     "Scope depends on facts not stated in the clause."),
    (r"\bcertain\b", "Unclear scope", "'Certain' entities/requirements are not enumerated."),
    (r"\bperiodic(ally)?\b", "Unclear frequency", "Frequency is not specified."),
    (r"operationali[sz]ation|date of (launch|commencement)", "Deadline tied to external event",
     "Deadline is relative to an event whose date must be confirmed."),
    (r"\bnecessary\b", "Undefined standard", "What is 'necessary' must be decided by the entity."),
    (r"who wish(es)? to|if (it|they) (choose|opt)", "Conditional applicability",
     "Applies only if the entity opts into the activity - confirm whether we do."),
    (r"\bpromptly\b|\btimely\b|without delay", "Unquantified timeline", "No measurable timeframe given."),
]

NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
    "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "fifteen": 15, "thirty": 30, "sixty": 60, "ninety": 90,
}


def find_entities(text: str) -> list[str]:
    found = []
    for key, pats in ENTITY_PATTERNS.items():
        for p in pats:
            if re.search(p, text, flags=re.I if not re.search(r"[A-Z]{2}", p) else 0):
                found.append(key)
                break
    # "brokers which are also banks" mentions bank as a qualifier only
    if "bank" in found and re.search(r"(broker|participant)s? (which|that|who) (is|are) also bank", text, re.I):
        found.remove("bank")
    if "bank" in found and re.search(r"bank accounts?", text, re.I) and not re.search(r"\bbanks?\b(?! account)", text, re.I):
        found.remove("bank")
    return found


def classify_category(text: str) -> str:
    for cat, pat in CATEGORY_RULES:
        if re.search(pat, text, re.I):
            return cat
    return "General Compliance"
