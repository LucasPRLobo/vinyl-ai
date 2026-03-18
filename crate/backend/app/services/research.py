"""AI-powered research synthesis using Claude API."""

import json

import anthropic

from app.config import settings
from app.prompts.smart_add import SYNTHESIS_SYSTEM, SYNTHESIS_PROMPT, INSIGHT_ON_ADD_PROMPT
from app.prompts.nl_to_cypher import (
    NL_TO_CYPHER_SYSTEM,
    NL_TO_CYPHER_PROMPT,
    RESPONSE_SYNTHESIS_PROMPT,
)


def _get_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=settings.anthropic_api_key)


def synthesize_record_data(
    artist: str,
    title: str,
    discogs_data: str,
    musicbrainz_data: str,
    additional_research: str = "None available.",
) -> dict:
    """Take raw data from multiple sources and synthesize into structured graph entities."""
    client = _get_client()

    prompt = SYNTHESIS_PROMPT.format(
        artist=artist,
        title=title,
        discogs_data=discogs_data,
        musicbrainz_data=musicbrainz_data,
        additional_research=additional_research,
    )

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=SYNTHESIS_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )

    response_text = message.content[0].text

    # Extract JSON from response (may be wrapped in ```json ... ```)
    json_str = _extract_json(response_text)
    return json.loads(json_str)


def generate_insights_on_add(
    record_summary: str,
    connections: str,
    collection_stats: str,
) -> list[dict]:
    """Generate 'Did you know?' insights when a record is added."""
    client = _get_client()

    prompt = INSIGHT_ON_ADD_PROMPT.format(
        record_summary=record_summary,
        connections=connections,
        collection_stats=collection_stats,
    )

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    response_text = message.content[0].text
    json_str = _extract_json(response_text)
    return json.loads(json_str)


def nl_to_cypher(question: str, group_id: str | None = None) -> str:
    """Translate a natural language question into a Cypher query."""
    client = _get_client()

    group_context = f", group_id = $group_id" if group_id else ""
    prompt = NL_TO_CYPHER_PROMPT.format(question=question, group_context=group_context)

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=NL_TO_CYPHER_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )

    cypher = message.content[0].text.strip()
    # Strip markdown code fences if present
    if cypher.startswith("```"):
        lines = cypher.split("\n")
        cypher = "\n".join(lines[1:-1])
    return cypher


def synthesize_query_response(question: str, raw_results: str) -> str:
    """Take raw Cypher results and generate a natural language response."""
    client = _get_client()

    prompt = RESPONSE_SYNTHESIS_PROMPT.format(question=question, results=raw_results)

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )

    return message.content[0].text


def _extract_json(text: str) -> str:
    """Extract JSON from a response that may contain markdown code fences."""
    if "```json" in text:
        start = text.index("```json") + 7
        end = text.index("```", start)
        return text[start:end].strip()
    if "```" in text:
        start = text.index("```") + 3
        end = text.index("```", start)
        return text[start:end].strip()
    return text.strip()
