# ResearchBot – Multi-Agent Research System

## Setup

### 1. Klonuj repo a nainstaluj závislosti
```bash
git clone https://github.com/mildovec01/research-agent.git
cd research-agent
pip install -r requirements.txt
```

### 2. Vytvoř .env soubor
```bash
cp .env.example .env
```
Vyplň všechny hodnoty v `.env`.

**Jak zjistit Discord channel ID:**
- Zapni Developer Mode v Discordu (Settings → Advanced → Developer Mode)
- Pravý klik na kanál → Copy Channel ID

### 3. Spusť bota

**Manuální test (okamžitý run):**
```bash
python main.py --now
```

**Normální běh (daily schedule):**
```bash
python main.py
```

**Jako systemd service na RPi:**
```bash
sudo nano /etc/systemd/system/researchbot.service
```
```ini
[Unit]
Description=ResearchBot Multi-Agent System
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/research_agent
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```
```bash
sudo systemctl enable researchbot
sudo systemctl start researchbot
sudo systemctl status researchbot
```

## Struktura projektu
```
research_agent/
├── main.py                  # vstupní bod
├── config.py                # nastavení
├── requirements.txt
├── .env                     # API klíče (nikdy do gitu!)
├── .gitignore
├── agents/
│   ├── orchestrator.py      # koordinátor
│   ├── research.py          # web search + RSS
│   ├── competitor.py        # market analysis
│   └── synthesis.py         # agregace + report
├── tools/
│   ├── search.py            # Tavily wrapper
│   ├── rss.py               # RSS reader
│   └── discord_bot.py       # Discord bot
├── memory/
│   └── state.py             # SQLite cache
└── reports/                 # vygenerované .md reporty
```

## Discord slash příkazy
- `/research <topic>` – spustí on-demand research pro dané téma

## Přidání vlastních témat
Uprav `config.py`:
- `RESEARCH_TOPICS` – témata pro daily research
- `COMPETITOR_COMPANIES` – firmy ke sledování
- `RSS_FEEDS` – RSS zdroje
