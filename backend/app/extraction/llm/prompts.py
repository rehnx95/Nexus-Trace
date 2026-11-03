EXTRACTION_PROMPT = """Extract crime-network information from the supplied text.

Use only these entity types: Person, Location, Organization, Vehicle, Phone, BankAccount.
Use only these relationship types: INTERCEPTED_CALL, ASSOCIATE_OF, FINANCIAL_TRAIL,
SPOTTED_AT, OWNS_VEHICLE, USES_DEVICE.

Rules:
- Return JSON only.
- Every entity id and edge endpoint must be grounded by an exact substring in the text.
- Do not invent values.
- Include normalized Indian phone IDs as +91XXXXXXXXXX where present.
- Include vehicles in uppercase alphanumeric form.
- Return this exact top-level JSON shape, with short arrays as needed:
  - `entities`: objects containing `type` and `id`
  - `edges`: objects containing `source_type`, `source_id`, `target_type`, `target_id`, and `type`

Text:
{text}
"""


def build_extraction_prompt(text: str) -> str:
    return EXTRACTION_PROMPT.replace("{text}", text)
