import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_GUILD_ID = int(os.getenv("DISCORD_GUILD_ID", "0"))
DISCORD_CHANNEL_ROBOTIKA = int(os.getenv("DISCORD_CHANNEL_ROBOTIKA", "0"))
DISCORD_CHANNEL_MARKET = int(os.getenv("DISCORD_CHANNEL_MARKET", "0"))
DISCORD_CHANNEL_PROJEKTY = int(os.getenv("DISCORD_CHANNEL_PROJEKTY", "1500556429067686011"))

RSS_FEEDS = [
    "https://news.google.com/rss/search?q=autonomous+robots&hl=en",
    "https://news.google.com/rss/search?q=autonomous+vehicles&hl=en",
    "https://news.google.com/rss/search?q=robotics+industry&hl=en",
    "https://feeds.feedburner.com/IeeeSpectrumFullText",
]

RESEARCH_TOPICS = [
    "autonomous agricultural robots",
    "ROS2 robotics latest developments",
    "LiDAR sensor technology 2025",
    "autonomous vehicle market trends",
]

COMPETITOR_COMPANIES = [
    "Boston Dynamics",
    "ABB Robotics",
    "KUKA",
    "Fanuc",
    "Universal Robots",
]

SCHEDULE_HOUR = 8
SCHEDULE_MINUTE = 0
