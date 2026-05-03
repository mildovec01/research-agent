import anthropic
import json
from config import ANTHROPIC_API_KEY, COMPETITOR_COMPANIES
from tools.search import search_company

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """Jsi market intelligence agent specializovaný na robotický průmysl.
Analyzuješ aktivity konkurenčních firem a tržní trendy.
Vždy odpovídej POUZE validním JSON bez markdown bloků."""

def run(companies: list[str] | None = None) -> dict:
    if companies is None:
        companies = COMPETITOR_COMPANIES

    company_data = []
    for company in companies:
        print(f"[Competitor] Analyzuji: {company}")
        data = search_company(company)
        company_data[company] = data

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
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
    return json.loads(raw)