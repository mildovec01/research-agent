import anthropic
import json
from config import ANTHROPIC_API_KEY
from tools.search import web_search

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """Jsi expert inženýr a návrhář embedded systémů a robotiky.
Dostaneš popis projektu a tvým úkolem je navrhnout kompletní technické řešení.

Vždy odpovídej POUZE validním JSON bez markdown bloků ani žádného jiného textu."""


def run(project_description: str) -> dict:
    print(f"[Project] Navrhuji projekt: {project_description}")

    print("[Project] Hledám součástky a ceny...")
    search_results = []
    search_results.extend(web_search(f"{project_description} components parts list microcontroller", max_results=5))
    search_results.extend(web_search(f"{project_description} Arduino ESP32 price components TME", max_results=4))
    search_results.extend(web_search(f"{project_description} OpenSCAD 3D model design", max_results=3))

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"""Navrhni kompletní projekt pro: "{project_description}"

Vrať JSON v přesně tomto formátu:
{{
  "project_name": "Název projektu",
  "description": "Stručný popis co projekt dělá",
  "microcontroller": {{
    "name": "např. Arduino Nano",
    "reason": "Proč byl vybrán"
  }},
  "components": [
    {{
      "name": "Název součástky",
      "quantity": 1,
      "unit_price_czk": 45,
      "total_price_czk": 45,
      "purpose": "K čemu slouží"
    }}
  ],
  "total_price_czk": 350,
  "openscad_code": "// OpenSCAD kód\\nmodule base() {{ ... }}\\n...",
  "main_code": "// Arduino/ROS2/Python kód\\n...",
  "code_language": "arduino|python|ros2",
  "assembly_steps": ["Krok 1", "Krok 2"],
  "warnings": ["Pozor na napájení 5V", "..."]
}}

Webové výsledky pro reference cen a součástek:
{json.dumps(search_results, ensure_ascii=False)}

DŮLEŽITÉ pro OpenSCAD:
- Vytvoř reálný funkční model s rozměry mikrokontroléru
- Zahrň mounting holes
- Zahrň místo pro všechny hlavní součástky
- Kód musí být spustitelný v OpenSCAD

DŮLEŽITÉ pro kód:
- Kompletní funkční kód, ne jen ukázka
- Komentáře v češtině
- Zahrň všechny piny a zapojení"""
        }]
    )

    raw = response.content[0].text.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(raw)
