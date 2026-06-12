"""
services/kb_generator.py
KB article generation wrapper and prompt template.
"""
from .llm_client import call_llm
from .anonymizer import anonymize

PROMPT_TEMPLATE = """Incident Resolution Notes:

{incident}

Convert these notes into a complete, standardized Knowledge Base article in Markdown.

Use the exact structure below, and include a review checklist and connector reference section:

# <Concise Descriptive Title>

**Category:** <Network / Database / Application / Auth / Storage / OS / Security>
**Severity:** <Low | Medium | High | Critical>
**Tags:** <comma-separated keywords>

## Summary
2-3 sentence description of the problem and resolution.

## Symptoms
- Bullet list of all observable symptoms reported

## Root Cause
Clear technical explanation of the underlying cause.

## Resolution Steps
1. Numbered, reproducible steps.
2. Include exact commands in code blocks where relevant.
```bash
# example command
```

## Validation Steps
How to confirm the fix is working correctly.

## Preventive Measures
- Bullet list of actions to prevent recurrence.

## Affected Systems
- List of systems, services, or components involved.

## References
- Related runbooks, documentation, or tickets (or "N/A").

## Review Checklist
- Review status: Pending
- Review due date: 6 months after approval
- Reviewer: Knowledge Manager

## Connector References
- Jira ticket: Not specified.
- ServiceNow record: Not specified.
- Confluence page: Not specified.

If some details are missing, write "Not specified." Do not invent details.
"""


def generate_kb_article(incident_text: str) -> str:
    cleaned = anonymize(incident_text)
    if not cleaned.strip():
        return "[ERROR] Incident text cannot be empty."
    prompt = PROMPT_TEMPLATE.format(incident=cleaned)
    return call_llm(prompt)
