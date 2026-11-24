"""SERA deterministic analysis engine.

Turns a parsed circular into obligations, applicability, ambiguity flags,
risk, impact map, SOP amendments and an implementation plan - with every
finding citing its paragraph and quoting the source sentence verbatim.

It needs no network or model, so it works on air-gapped / on-prem installs.
When an LLM is configured (see llm.py) the LLM *proposes* obligations and
this module *verifies and enriches* them (citation check, applicability,
risk, impact, plan).
"""
from __future__ import annotations

import re
from datetime import date, timedelta
from typing import Any

from app.engine import taxonomy as tx
from app.engine.text import DATE_RE, Paragraph, ParsedCircular, to_iso

MODAL_RE = re.compile(
    r"\b(shall not|must not|shall|must|should|(?:is|are) (?:required|mandated|directed|obligated) to|"
    r"required to|need to|it is mandatory|are hereby directed to|is hereby directed to)\b",
    re.I,
)
EXEMPT_RE = re.compile(r"shall not be applicable|not be applicable|is not applicable|exempt(ed|ion)?\b|doing away|"
                       r"stand(s)? deleted|^deleted$", re.I)
CHANGE_RE = re.compile(r"(decided to (extend|revise|modify|relax)|extend(ed)? the timeline|come into force|"
                       r"with effect from|stand(s)? amended)", re.I)
HISTORICAL_RE = re.compile(r"^(SEBI (has )?vide|SEBI has specified|In terms of|As per para|Subsequently, SEBI|"
                           r"SEBI,? vide|Further, as per para)", re.I)
BOILERPLATE_RE = re.compile(r"issued in exercise of powers|available on (the )?SEBI website|"
                            r"representations? (has|have) been received|In this regard|it has been decided to modify|"
                            r"continue to (remain|be) (applicable|in force)|remain(s)? unchanged",
                            re.I)
FREQ_RE = re.compile(r"\b(daily|weekly|fortnightly|monthly|quarterly|half[- ]yearly|annually|yearly|"
                     r"every \w+ (?:months?|years?|days?))\b", re.I)
REL_RE = re.compile(r"within (\d+|" + "|".join(tx.NUMBER_WORDS) + r")\s+(working days?|days?|weeks?|months?)", re.I)
DEADLINE_PREFIX_RE = re.compile(r"(by|until|till|before|on or before|not later than|latest by|from|"
                                r"with effect from|w\.e\.f\.?)\s*$", re.I)
STOPWORDS = set("the a an of to and or for in on by with as is are be shall must should which that this from at "
                "their its any all such other also under said above below new existing".split())


# ── helpers ────────────────────────────────────────────────────────────────
def _tokens(s: str) -> set[str]:
    return {w for w in re.findall(r"[a-z]{3,}", s.lower()) if w not in STOPWORDS}


def _jaccard(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    return len(ta & tb) / max(1, len(ta | tb))


def _overlap(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    return len(ta & tb) / max(1, min(len(ta), len(tb)))


PENALTY_RE = re.compile(r"(shall|will) attract (penal|penalty)|penal action|liable (to|for) (penalty|action)", re.I)
LEAD_RE = re.compile(r"^(however|further(more)?|accordingly|additionally|also|subsequently|in terms of [^,]+|"
                     r"as per [^,]+|in this regard)\s*,\s*", re.I)


def _subject(sentence: str) -> str:
    m = MODAL_RE.search(sentence)
    subj = sentence[:m.start()] if m else ""
    return LEAD_RE.sub("", subj.strip())


def _num(word: str) -> int:
    return int(word) if word.isdigit() else tx.NUMBER_WORDS.get(word.lower(), 0)


def _add(d: date, n: int, unit: str) -> date:
    unit = unit.lower()
    if unit.startswith("working"):
        return d + timedelta(days=round(n * 7 / 5))
    if unit.startswith("day"):
        return d + timedelta(days=n)
    if unit.startswith("week"):
        return d + timedelta(weeks=n)
    return d + timedelta(days=30 * n)


def extract_deadline(sentence: str, base: date | None) -> tuple[str | None, date | None, str | None]:
    """Returns (deadline_text, due_date, frequency)."""
    freq_m = FREQ_RE.search(sentence)
    frequency = freq_m.group(1).lower() if freq_m else None
    best: tuple[str, date] | None = None
    for m in DATE_RE.finditer(sentence):
        prefix = sentence[max(0, m.start() - 25):m.start()]
        if DEADLINE_PREFIX_RE.search(prefix) and not re.search(r"dated\s*$", prefix, re.I):
            iso = to_iso(m)
            if iso:
                d = date.fromisoformat(iso)
                kw = DEADLINE_PREFIX_RE.search(prefix).group(1)
                best = (f"{kw} {m.group(0)}", d)
    if best:
        return best[0], best[1], frequency
    rm = REL_RE.search(sentence)
    if rm:
        n = _num(rm.group(1))
        rest = sentence[rm.end():]
        text = rm.group(0)
        # "within 7 working days of its closure" is a recurring, event-driven SLA - not a one-off deadline
        anchored_to_circular = re.match(r"\s*(of|from|after)\s+(the\s+)?(date of\s+)?(this circular|issuance|issue of this)", rest, re.I)
        if re.match(r"\s*(of|from|after)\b", rest, re.I) and not anchored_to_circular:
            event = re.match(r"\s*((?:of|from|after)\s+[^,.;]{3,60})", rest, re.I)
            return f"{text} {event.group(1).strip() if event else ''}".strip(), None, frequency or "event-driven SLA"
        due = _add(base, n, rm.group(2)) if base and n else None
        return text, due, frequency
    return None, None, frequency


def detect_ambiguity(sentence: str, deadline_text: str | None) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    seen = set()
    for pat, kind, why in tx.AMBIGUITY_TERMS:
        m = re.search(pat, sentence, re.I)
        if m and kind not in seen:
            seen.add(kind)
            out.append({
                "term": m.group(0),
                "type": kind,
                "explanation": why,
                "question": f"Clarify '{m.group(0)}' in: \"{sentence[:140]}...\"" if len(sentence) > 140
                else f"Clarify '{m.group(0)}' in: \"{sentence}\"",
            })
    return out


def _action_phrase(sentence: str) -> str:
    m = MODAL_RE.search(sentence)
    tail = sentence[m.end():] if m else sentence
    # passive voice: "all demat accounts ... should be appropriately tagged"
    #   -> "Ensure all demat accounts ... are appropriately tagged"
    pm = re.match(r"\s*be\s+((?:\w+ly\s+)?\w+(?:ed|en|ne)\b.*)", tail, re.I)
    subj = _subject(sentence)
    if pm and re.match(r"(required|mandated|directed|obligated|permitted|allowed)\b", pm.group(1), re.I):
        pm = None
    if m and pm and subj and len(subj) < 140:
        head = re.split(r" which | maintained | that | of ", subj)[0]
        verb = "are" if re.search(r"s\b", head) else "is"
        return f"Ensure {subj[:1].lower() + subj[1:]} {verb} {pm.group(1).strip(' .;:,')}"
    tail = re.sub(r"^\s*(be required to|be|ensure that|ensure)\s+", lambda x: "Ensure " if "ensure" in x.group(0).lower() else "", tail, flags=re.I)
    tail = tail.strip(" :;,.")
    if m and m.group(1).lower() in ("shall not", "must not"):
        tail = "Do not " + tail
    return tail[:1].upper() + tail[1:] if tail else sentence


def _shorten(s: str, n: int = 96) -> str:
    s = re.sub(r"\s*\([^)]{0,40}\)", "", s)  # drop parenthetical abbreviations
    s = re.sub(r"\s+", " ", s).strip()
    if len(s) <= n:
        return s
    cut = s[:n]
    for sep in [",", ";", " - ", " which ", " who ", " that "]:
        i = cut.rfind(sep)
        if i > n * 0.55:
            return cut[:i].strip()
    return cut.rsplit(" ", 1)[0] + "..."


PLURAL = {"Depository": "Depositories", "Mutual Fund / AMC": "Mutual Funds / AMCs", "Listed Entity": "Listed Entities",
          "KYC Registration Agency": "KRAs", "Credit Rating Agency": "Credit Rating Agencies"}


def _actor_label(entities: list[str]) -> str:
    labels = [PLURAL.get(tx.ENTITY_LABELS[e], tx.ENTITY_LABELS[e] + "s")
              for e in entities if e in tx.ENTITY_LABELS and e != "bank"]
    return " / ".join(labels[:2]) if labels else "Regulated entities"


# ── stage 1: obligations ───────────────────────────────────────────────────
def extract_candidates(circ: ParsedCircular) -> list[dict[str, Any]]:
    """Find obligation-bearing sentences (with directive lists expanded)."""
    cands: list[dict[str, Any]] = []
    parents: dict[str, dict[str, Any]] = {}  # para number -> {"actor_text", "verb"}
    for p in circ.paragraphs:
        # a paragraph that opens by recounting an earlier circular is context throughout
        para_historical = bool(p.sentences and HISTORICAL_RE.search(p.sentences[0]))
        # inherit directive lead-ins like "Stock Exchanges/Depositories are directed to:"
        parent = None
        if p.number and "." in p.number:
            parent = parents.get(p.number.rsplit(".", 1)[0])
        for s in p.sentences or [p.text]:
            if BOILERPLATE_RE.search(s) or len(s) < 20:
                continue
            if re.search(r"(directed to|shall ensure the following|it is prescribed that|following)\s*:?\s*$", s, re.I):
                parents[p.number or p.ref] = {"lead": s}
                continue
            kind = None
            if PENALTY_RE.search(s):
                kind = "penalty"
            elif EXEMPT_RE.search(s):
                kind = "exemption"
            elif CHANGE_RE.search(s):
                kind = "timeline_change"
            elif MODAL_RE.search(s):
                kind = "obligation"
            elif parent:
                kind = "obligation"
                s_lead = parent["lead"]
                s = f"{s_lead.rstrip(': ')} {s}"
            if not kind:
                continue
            cands.append({
                "paragraph": p,
                "sentence": s,
                "kind": kind,
                "historical": para_historical or bool(HISTORICAL_RE.search(s)),
            })
    return cands


def build_obligations(circ: ParsedCircular, org: dict[str, Any], *, today: date | None = None,
                      llm_proposals: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    today = today or date.today()
    circ_date = date.fromisoformat(circ.date) if circ.date else today
    addressee_entities = tx.find_entities(" ".join(circ.addressees)) if circ.addressees else []
    org_entities = set(org.get("entity_types") or [])
    effective_date: date | None = None
    for p in circ.paragraphs:
        m = re.search(r"(come into force|with effect from|effective from)[^.]*", p.text, re.I)
        if m:
            dm = DATE_RE.search(m.group(0))
            if dm and to_iso(dm):
                effective_date = date.fromisoformat(to_iso(dm))
    base = effective_date or circ_date

    cands = extract_candidates(circ)
    if llm_proposals:
        cands = _merge_llm(cands, llm_proposals, circ)

    penalties = [c for c in cands if c["kind"] == "penalty"]
    cands = [c for c in cands if c["kind"] != "penalty"]
    items: list[dict[str, Any]] = []
    for c in cands:
        if c["kind"] == "timeline_change" and not re.search(r"extend|revise", c["sentence"], re.I):
            continue  # pure "comes into force" lines only set the base date
        p: Paragraph = c["paragraph"]
        s = c["sentence"]
        subj = _subject(s)
        entities = ([e for e in tx.find_entities(subj) if e != "bank"] if subj else []) \
            or [e for e in tx.find_entities(s) if e != "bank"] or [e for e in addressee_entities if e != "bank"]
        deadline_text, due, freq = extract_deadline(s, base)
        category = "Exemption" if c["kind"] == "exemption" else (c.get("category") or tx.classify_category(s))
        action = c.get("action") or (_action_phrase(s) if c["kind"] != "exemption" else s)
        if c.get("title"):
            title = c["title"]
        elif c["kind"] == "exemption":
            title = f"Exemption: {_shorten(LEAD_RE.sub('', s))}"
        elif c["kind"] == "timeline_change":
            title = f"Revised timeline: {_shorten(LEAD_RE.sub('', s))}"
        else:
            title = f"{_actor_label(entities)}: {_shorten(action)}"
        items.append({
            "kind": c["kind"],
            "paragraph_ref": p.ref,
            "page": p.page,
            "source_text": s,
            "historical": c["historical"],
            "entities": entities,
            "category": category,
            "title": title,
            "action": action,
            "deadline_text": deadline_text,
            "due_date": due,
            "frequency": freq,
            "verified_citation": True,
            "origin": c.get("origin", "rules"),
        })

    # Supersede: a later sentence restating the same requirement replaces the earlier one
    kept: list[dict[str, Any]] = []
    for it in items:
        dup = next((k for k in kept if it["kind"] == k["kind"] and it["category"] == k["category"]
                    and _overlap(it["action"], k["action"]) >= (0.45 if k["historical"] else 0.75)), None)
        if dup:
            dup.setdefault("supersedes", []).append(dup["paragraph_ref"])
            for key in ("paragraph_ref", "page", "source_text", "historical", "title", "action"):
                dup[key] = it[key]
            if it["due_date"]:
                dup["deadline_text"], dup["due_date"] = it["deadline_text"], it["due_date"]
            continue
        kept.append(it)

    # Apply timeline extensions to the obligations they modify
    for ch in [k for k in kept if k["kind"] == "timeline_change" and k["due_date"]]:
        topic = (circ.subject or "") + " " + ch["source_text"]
        for ob in kept:
            if ob is ch or ob["kind"] != "obligation":
                continue
            if len(_tokens(topic) & _tokens(ob["source_text"])) >= 2:
                ob["deadline_text"] = f"{ch['deadline_text']} (extended per {ch['paragraph_ref']})"
                ob["due_date"] = ch["due_date"]
                ob["extended_by"] = ch["paragraph_ref"]
                new_date = DATE_RE.search(ch["deadline_text"] or "")
                if new_date:
                    for key in ("title", "action"):
                        ob[key] = DATE_RE.sub(new_date.group(0), ob[key], count=1)
                ch["applied_to"] = True
    kept = [k for k in kept if not (k["kind"] == "timeline_change" and k.get("applied_to"))]

    has_current = any(k["kind"] == "obligation" and not k["historical"] for k in kept)

    # finalize: applicability, ambiguity, risk, evidence
    result: list[dict[str, Any]] = []
    for i, ob in enumerate(kept, start=1):
        s = ob["source_text"]
        context_only = ob["historical"] and has_current and not ob.get("extended_by")
        direct = sorted(set(ob["entities"]) & org_entities)
        mentioned = sorted(set(tx.find_entities(s)) & org_entities)
        if context_only:
            applicable, conf = False, 0.6
            reason = ("Restates an existing requirement for context; this circular modifies it elsewhere. "
                      "Kept for traceability - include it if your team disagrees.")
        elif direct:
            applicable, conf = True, 0.9
            reason = f"Directly addressed to {', '.join(tx.ENTITY_LABELS[e] for e in direct)} - your organisation is registered as one."
        elif mentioned:
            applicable, conf = True, 0.65
            reason = (f"Obligation sits with {_actor_label(ob['entities'])}, but it concerns "
                      f"{', '.join(tx.ENTITY_LABELS[e] for e in mentioned)} - indirect impact on you.")
        elif not ob["entities"]:
            applicable, conf = True, 0.5
            reason = "No specific entity named; treated as applicable pending review."
        else:
            applicable, conf = False, 0.85
            reason = f"Addressed to {_actor_label(ob['entities'])}; your registered entity types are not covered."
        ambiguity = detect_ambiguity(s, ob["deadline_text"])
        risk_score = tx.CATEGORY_WEIGHT.get(ob["category"], 1)
        if re.search(r"\b(shall|must)\b", s, re.I):
            risk_score += 1
        if re.search(r"non-?compliance|penal|action (shall|will) be taken|disciplinary", s, re.I) or penalties:
            risk_score += 1
        overdue = False
        if ob["due_date"]:
            days = (ob["due_date"] - today).days
            if days < 0:
                risk_score += 2
                overdue = True
            elif days <= 30:
                risk_score += 2
            elif days <= 90:
                risk_score += 1
        if ob["kind"] == "exemption":
            risk_score = min(risk_score, 1)
        if not applicable:
            risk_score = min(risk_score, 1)
        risk = "LOW" if risk_score <= 1 else "MEDIUM" if risk_score <= 3 else "HIGH" if risk_score == 4 else "CRITICAL"
        result.append({
            "seq": i,
            **{k: v for k, v in ob.items() if k not in ("entities",)},
            "entities": [tx.ENTITY_LABELS.get(e, e) for e in ob["entities"]],
            "context_only": context_only,
            "due_date": ob["due_date"].isoformat() if ob["due_date"] else None,
            "overdue": overdue,
            "applicable": applicable,
            "applicability_reason": reason,
            "applicability_confidence": conf,
            "ambiguity": ambiguity,
            "risk": risk,
            "evidence": tx.EVIDENCE_BY_CATEGORY.get(ob["category"], tx.EVIDENCE_BY_CATEGORY["General Compliance"]),
            "confidence": round(0.55 + 0.1 * (ob["kind"] == "obligation") + 0.15 * bool(re.search(r"\b(shall|must)\b", s, re.I))
                                - 0.1 * len(ambiguity) + (0.1 if ob.get("origin") == "llm+verified" else 0), 2),
        })
        result[-1]["confidence"] = max(0.3, min(0.97, result[-1]["confidence"]))

    applicable_n = sum(1 for r in result if r["applicable"])
    amb_n = sum(1 for r in result if r["ambiguity"])
    dues = sorted(r["due_date"] for r in result if r["due_date"] and r["applicable"])
    doc_risk = max((r["risk"] for r in result if r["applicable"]), key=lambda x: ["LOW", "MEDIUM", "HIGH", "CRITICAL"].index(x), default="LOW")
    summary = (
        f"{circ.subject or 'Regulatory circular'}. SERA identified {len(result)} requirement(s), "
        f"{applicable_n} applicable to your organisation"
        + (f", {amb_n} needing interpretation" if amb_n else "")
        + (f". Earliest applicable deadline: {dues[0]}." if dues else ".")
    )
    return {
        "obligations": result,
        "summary": summary,
        "risk": doc_risk,
        "effective_date": effective_date.isoformat() if effective_date else None,
        "addressees": circ.addressees,
        "addressee_entities": [tx.ENTITY_LABELS.get(e, e) for e in addressee_entities],
        "penalty_clauses": [{"paragraph_ref": c["paragraph"].ref, "text": c["sentence"]} for c in penalties],
    }


def _merge_llm(cands: list[dict[str, Any]], proposals: list[dict[str, Any]], circ: ParsedCircular) -> list[dict[str, Any]]:
    """LLM proposals are accepted only if their quote is found verbatim in the cited paragraph."""
    norm = lambda t: re.sub(r"[^a-z0-9]", "", t.lower())  # noqa: E731
    by_ref = {p.ref: p for p in circ.paragraphs}
    merged = []
    for prop in proposals:
        quote = prop.get("source_quote") or ""
        para = by_ref.get(prop.get("paragraph_ref") or "")
        if para is None:
            para = next((p for p in circ.paragraphs if norm(quote)[:60] and norm(quote)[:60] in norm(p.text)), None)
        if para is None or not quote or norm(quote) not in norm(para.text):
            continue  # hallucination guard: drop unverifiable citations
        merged.append({
            "paragraph": para, "sentence": quote, "kind": prop.get("kind") or "obligation",
            "historical": bool(HISTORICAL_RE.search(quote)), "title": prop.get("title"),
            "action": prop.get("action"), "category": prop.get("category"), "origin": "llm+verified",
        })
    # keep rule-found candidates the LLM missed (recall safety net)
    for c in cands:
        if not any(_jaccard(c["sentence"], m["sentence"]) > 0.5 for m in merged):
            merged.append(c)
    merged.sort(key=lambda c: circ.paragraphs.index(c["paragraph"]))
    return merged


# ── stage 2: impact, SOPs, plan ────────────────────────────────────────────
def _match_dept(name: str, org_depts: list[str]) -> str | None:
    n = name.lower()
    for d in org_depts:
        dl = d.lower()
        if dl == n or dl.split(" ")[0] == n.split(" ")[0]:
            return d
    return None


def impact_map(obligations: list[dict[str, Any]], org: dict[str, Any]) -> dict[str, Any]:
    org_depts = org.get("departments") or tx.DEFAULT_DEPARTMENTS
    org_systems = org.get("systems") or tx.DEFAULT_SYSTEMS
    mappings, review = [], []
    for ob in obligations:
        if not ob["applicable"] or ob.get("excluded"):
            continue
        s = ob["source_text"] + " " + ob["title"]
        depts: list[str] = []
        for pat, ds in tx.DEPT_RULES:
            if re.search(pat, s, re.I):
                depts += [d for d in ds if d not in depts]
        if ob.get("kind") == "exemption" or ob.get("category") == "Exemption":
            depts = ["Compliance"] + [d for d in depts if d != "Compliance"]
        if "Compliance" not in depts:
            depts.append("Compliance")
        resolved = []
        for idx, d in enumerate(depts[:4]):
            match = _match_dept(d, org_depts)
            role = "primary_owner" if idx == 0 else ("informed" if d == "Compliance" and idx > 1 else "contributor")
            if match is None:
                review.append({"obligation": ob["code"], "reason": f"No department in your org profile matches '{d}'."})
            resolved.append({"department": match or d, "matched": match is not None, "role": role})
        systems = []
        for pat, sysname in tx.SYSTEM_RULES:
            if re.search(pat, s, re.I) and sysname in org_systems and sysname not in systems:
                systems.append(sysname)
        mappings.append({
            "obligation_code": ob["code"],
            "obligation_title": ob["title"],
            "departments": resolved,
            "systems": systems,
            "severity": ob["risk"].lower(),
            "rationale": f"Mapped from keywords in {ob['paragraph_ref']} ({ob['category']}).",
        })
    # dependencies: obligations sharing a primary department are sequenced
    return {"mappings": mappings, "needs_review": review}


def sop_drafts(obligations: list[dict[str, Any]], impact: dict[str, Any], circ_ref: str) -> list[dict[str, Any]]:
    by_code = {o["code"]: o for o in obligations}
    drafts = []
    for m in impact["mappings"]:
        ob = by_code[m["obligation_code"]]
        owner = m["departments"][0]["department"]
        deadline = ob.get("deadline_text") or "as per the circular's effective date"
        steps = [
            f"1. Owner: {owner} (accountable); Compliance reviews.",
            f"2. Requirement: {ob['action']}",
            f"3. Timeline: {deadline}" + (f"; frequency: {ob['frequency']}" if ob.get("frequency") else "") + ".",
            f"4. Systems/records affected: {', '.join(m['systems']) or 'none identified'}.",
            f"5. Evidence to retain: {ob['evidence']}.",
            "6. Escalation: exceptions reported to the Compliance Officer within 2 working days.",
        ]
        drafts.append({
            "obligation_code": ob["code"],
            "department": owner,
            "sop_title": f"{owner} SOP - {ob['category']}",
            "change_type": "Amend" if ob["kind"] == "exemption" or ob.get("extended_by") else "Add",
            "current_text": "No documented procedure currently covers this requirement." if ob["kind"] != "exemption"
            else "Existing procedure applies the requirement without the new exemption.",
            "proposed_text": "\n".join(steps),
            "citation": f"{circ_ref}, {ob['paragraph_ref']}",
        })
    return drafts


def implementation_plan(obligations: list[dict[str, Any]], impact: dict[str, Any], start: date) -> dict[str, Any]:
    by_code = {o["code"]: o for o in obligations}
    tasks = []
    for m in impact["mappings"]:
        ob = by_code[m["obligation_code"]]
        owner = m["departments"][0]["department"]
        due = date.fromisoformat(ob["due_date"]) if ob.get("due_date") else None
        late = due is not None and due < start + timedelta(days=21)
        final = due if due and not late else start + timedelta(days=21)

        def t(phase, title, dept, days, evidence=None, desc=None):
            d = min(start + timedelta(days=days), final) if not late else start + timedelta(days=max(2, days // 2))
            tasks.append({
                "obligation_code": ob["code"], "phase": phase, "title": title, "department": dept,
                "due_date": d.isoformat(), "priority": {"CRITICAL": "CRITICAL", "HIGH": "HIGH", "MEDIUM": "MEDIUM"}.get(ob["risk"], "LOW"),
                "evidence_requirement": evidence, "description": desc or ob["action"],
            })

        short = _shorten(ob["title"].split(": ", 1)[-1], 70)
        if ob["kind"] == "exemption":
            t("Assess", f"Confirm exemption applies to us: {short}", "Compliance", 5, ob["evidence"])
            continue
        t("Assess", f"Gap assessment: {short}", "Compliance", 4,
          "Gap assessment note", f"Compare current practice against {ob['paragraph_ref']}: \"{ob['source_text'][:220]}\"")
        cat = ob["category"]
        src = ob["source_text"].lower()
        if re.search(r"enrol|regist", src):
            cat = "Registration & Enrolment"
        elif re.search(r"tagg|nomenclature|named", src):
            cat = "Account Operations"
        elif re.search(r"report|inform|communicat|submit|provide details", src):
            cat = "Reporting & Disclosure"
        if cat == "Registration & Enrolment":
            impl = "Complete enrolment / registration and record the confirmation"
        elif cat == "Account Operations":
            impl = "Rename/tag affected bank & demat accounts per prescribed nomenclature"
        elif cat == "Reporting & Disclosure":
            impl = "Set up the required reporting/communication workflow"
        elif cat == "Governance":
            impl = "Amend policies / bye-laws and obtain approval"
        elif cat == "Timeline / Effective Date":
            impl = "Update compliance calendar with the revised timeline"
        else:
            impl = "Implement the process change"
        t("Implement", f"{impl} ({ob['code']})", owner, 12)
        for sysname in m["systems"][:1]:
            t("Implement", f"Configure {sysname} for {ob['code']}", "IT & Information Security", 14)
        t("Validate", f"Collect evidence & certify {ob['code']}", owner, 19, ob["evidence"])
    phases = [
        {"name": "Assess", "description": "Confirm interpretation and current-state gaps"},
        {"name": "Implement", "description": "Process, system and policy changes"},
        {"name": "Validate", "description": "Evidence collection and Compliance certification"},
    ]
    return {"start_date": start.isoformat(), "phases": phases, "tasks": tasks}
