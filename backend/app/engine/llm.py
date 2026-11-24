"""Optional LLM layer: the model *proposes* obligations, analyzer.py *verifies* them.

Provider chain: Anthropic (ANTHROPIC_API_KEY) -> Groq (GROQ_API_KEY) -> none.
With no key, or on any failure, SERA runs fully on its deterministic engine.
"""
from __future__ import annotations

import json
import logging
from typing import Literal

import httpx
from pydantic import BaseModel, Field

from app.core.config import settings
from app.engine.text import ParsedCircular

logger = logging.getLogger("sera.engine.llm")


class ProposedObligation(BaseModel):
    paragraph_ref: str = Field(description="Paragraph reference exactly as given, e.g. 'Para 3' or 'Para 15.3.4'")
    source_quote: str = Field(description="The exact sentence copied verbatim from that paragraph")
    kind: Literal["obligation", "exemption", "timeline_change"]
    title: str = Field(description="Short actionable title, prefixed with the actor, e.g. 'Stock Brokers: Report ...'")
    action: str = Field(description="What must be done, in imperative form")
    category: str


class ObligationProposals(BaseModel):
    obligations: list[ProposedObligation]


SYSTEM = (
    "You are a SEBI regulatory compliance analyst. From the numbered paragraphs of a circular, list every "
    "requirement that imposes a duty (obligation), grants a relaxation (exemption), or changes a timeline "
    "(timeline_change). Rules: copy source_quote VERBATIM from the cited paragraph; never invent deadlines, "
    "owners or requirements; skip boilerplate (powers conferred, website availability, background narrative). "
    "Categories: Cybersecurity, Registration & Enrolment, Account Operations, Reporting & Disclosure, "
    "Record Keeping, Client Protection, Governance, Timeline / Effective Date, General Compliance."
)


def provider_name() -> str:
    if settings.anthropic_api_key:
        return f"anthropic:{settings.anthropic_model}"
    if settings.GROQ_API_KEY:
        return f"groq:{settings.LLM_MODEL}"
    return "offline"


def _prompt(circ: ParsedCircular) -> str:
    paras = "\n".join(f"[{p.ref}] {p.text}" for p in circ.paragraphs)
    return f"Subject: {circ.subject}\nAddressees: {', '.join(circ.addressees)}\n\nParagraphs:\n{paras}"


async def propose_obligations(circ: ParsedCircular) -> tuple[list[dict] | None, str]:
    """Returns (proposals or None, provider used). Never raises."""
    name = provider_name()
    if name == "offline" or not circ.paragraphs:
        return None, "offline"
    try:
        if name.startswith("anthropic"):
            import anthropic

            client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
            resp = await client.messages.parse(
                model=settings.anthropic_model,
                max_tokens=16000,
                system=SYSTEM,
                messages=[{"role": "user", "content": _prompt(circ)}],
                output_format=ObligationProposals,
            )
            if resp.stop_reason == "refusal" or resp.parsed_output is None:
                logger.warning("anthropic returned no parsed output (stop_reason=%s)", resp.stop_reason)
                return None, "offline"
            return [o.model_dump() for o in resp.parsed_output.obligations], name
        # Groq (OpenAI-compatible JSON mode)
        schema = json.dumps(ObligationProposals.model_json_schema())
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
                json={
                    "model": settings.LLM_MODEL,
                    "temperature": 0,
                    "response_format": {"type": "json_object"},
                    "messages": [
                        {"role": "system", "content": SYSTEM + "\nReturn JSON matching this schema:\n" + schema},
                        {"role": "user", "content": _prompt(circ)},
                    ],
                },
            )
            r.raise_for_status()
            data = ObligationProposals.model_validate_json(r.json()["choices"][0]["message"]["content"])
            return [o.model_dump() for o in data.obligations], name
    except Exception as exc:  # noqa: BLE001 - any provider failure degrades to the offline engine
        logger.warning("LLM proposal failed (%s); falling back to offline engine", exc)
        return None, "offline"
