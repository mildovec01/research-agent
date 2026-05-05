import anthropic
import json
from config import ANTHROPIC_API_KEY, COMPETITOR_COMPANIES
from tools.search import search_company
from json_repair import repair_json

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """Jsi market intelligence agent specializovaný na robotický průmysl.
Analyzuješ aktivity konkurenčních firem a tržní trendy.
Vždy odpovídej POUZE validním JSON bez markdown bloků."""


def run(companies: list[str] | None = None) -> dict:
    if companies is None:
        companies = COMPETITOR_COMPANIES

    company_data = {}
    for company in companies:
        print(f"[Competitor] Analyzuji: {company}")
        results = search_company(company)
        company_data[company] = results

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"""Analyzuj aktivity těchto firem a vrať JSON ve formátu:
{{
  "company_updates": [
    {{
      "company": "...",
      "headline": "...",
      "impact": "high|medium|low",
      "summary": "...",
      "url": "..."
    }}
  ],
  "market_trends": ["trend1", "trend2"],
  "opportunities": ["opportunity1"]
}}

Data: {json.dumps(company_data, ensure_ascii=False)}"""
        }]
    )

    raw = response.content[0].text.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    # ořízni na poslední platný JSON
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        last_brace = raw.rfind("}")
        if last_brace != -1:
            raw = raw[:last_brace+1]
        return json.loads(repair_json(raw))
