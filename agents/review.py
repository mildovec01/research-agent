import anthropic
import json
from config import ANTHROPIC_API_KEY
from tools.search import web_search

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """Jsi přísný technický reviewer a inženýr s 20 lety zkušeností.
Dostaneš návrh projektu od jiného agenta a tvým úkolem je:
1. Zkontrolovat technickou správnost
2. Ověřit reálnost cen (orientačně)
3. Zkontrolovat OpenSCAD kód
4. Zkontrolovat hlavní kód
5. Opravit chyby a vylepšit návrh

Buď kritický ale konstruktivní. Vždy odpovídej POUZE validním JSON bez markdown bloků."""


def run(project_data: dict) -> dict:
    print("[Review] Kontroluji návrh projektu...")

    project_name = project_data.get("project_name", "projekt")
    search_results = web_search(
        f"{project_name} {project_data.get('microcontroller', {}).get('name', '')} price specifications",
        max_results=4
    )

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"""Zkontroluj a vylepši tento návrh projektu.

Vrať JSON ve stejném formátu jako vstup, ale opravený a vylepšený.
Přidej navíc tato pole:
{{
  ...původní pole opravená...,
  "review_notes": ["Co bylo opraveno/vylepšeno"],
  "confidence_score": 8,
  "approved": true
}}

Zkontroluj zejména:
- Jsou ceny reálné? (TME, Aliexpress orientace)
- Je OpenSCAD kód syntakticky správný?
- Je hlavní kód funkční a kompletní?
- Jsou součástky kompatibilní?
- Nechybí něco důležitého?

Návrh k reviewu:
{json.dumps(project_data, ensure_ascii=False)}

Reference cen z webu:
{json.dumps(search_results, ensure_ascii=False)}"""
        }]
    )

    raw = response.content[0].text.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    result = json.loads(raw)
    print(f"[Review] Hotovo — confidence score: {result.get('confidence_score', '?')}/10")
    return result
