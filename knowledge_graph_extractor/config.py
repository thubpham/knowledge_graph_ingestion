from dotenv import load_dotenv
from google import genai
from falkordb.asyncio import FalkorDB
import os

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env")

ai_client = genai.Client(api_key=api_key)

db_client = FalkorDB(
    host="localhost",
    port=6379,
    username=None,
    password=None,
)