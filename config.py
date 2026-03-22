import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHILD_NAME = os.getenv("CHILD_NAME", "Ребёнок")
CHILD_AGE = int(os.getenv("CHILD_AGE", "10"))
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_TRANSACTIONS_DB = os.getenv("NOTION_TRANSACTIONS_DB")
NOTION_GOALS_DB = os.getenv("NOTION_GOALS_DB")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
