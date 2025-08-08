from __future__ import annotations

import random
import time
from datetime import datetime
from typing import Dict, List

from flask import Flask, jsonify, request
from flask_cors import CORS

import os
import itertools
from kg_extractor.config import api_key
import asyncio
from graphiti_core.driver.falkordb_driver import FalkorDriver
from graphiti_core.search.search_config_recipes import COMBINED_HYBRID_SEARCH_RRF
from graphiti_core import Graphiti
from graphiti_core.llm_client.config import LLMConfig
from graphiti_core.llm_client.gemini_client import GeminiClient
from graphiti_core.embedder.gemini import GeminiEmbedder, GeminiEmbedderConfig
from graphiti_core.cross_encoder.gemini_reranker_client import GeminiRerankerClient
from graphiti_core.driver.falkordb_driver import FalkorDriver
import itertools
from graphiti_core.driver.falkordb_driver import FalkorDriver
from graphiti_core.search.search_config_recipes import COMBINED_HYBRID_SEARCH_RRF
from graphiti_core import Graphiti
from graphiti_core.llm_client.config import LLMConfig
from graphiti_core.llm_client.gemini_client import GeminiClient
from graphiti_core.embedder.gemini import GeminiEmbedder, GeminiEmbedderConfig
from graphiti_core.cross_encoder.gemini_reranker_client import GeminiRerankerClient
from graphiti_core.driver.falkordb_driver import FalkorDriver
from query import search_graph_and_format_results
from kg_extractor.llm import generate_embedding, salvage_json

usr_falkor_driver = FalkorDriver(
	host='localhost',        
	port=6379,           
	username=None,         
	password=None,
	database="aug-8-db-tech-doc",       
)

usr_embed_client = GeminiEmbedder(
		config=GeminiEmbedderConfig(
			api_key=api_key,
			embedding_model="gemini-embedding-001",
		)
	)

usr_cross_encoder = GeminiRerankerClient(
		config=LLMConfig(
			api_key=api_key,
			model="gemini-2.0-flash-lite",
			temperature=0.3,
		)
	)

usr_llm_client = GeminiClient(
		config=LLMConfig(
			api_key=api_key,
			temperature=0.65,
			model="gemini-2.5-flash",
			small_model='gemini-2.5-flash-lite'
		))

usr_graphiti = Graphiti(
	graph_driver=usr_falkor_driver,
	llm_client=usr_llm_client,
	embedder=usr_embed_client,
	cross_encoder=usr_cross_encoder,)

app = Flask(__name__)

# --------------------------------------------------------------
# Enable CORS for *all* routes – you can tighten this later.
# --------------------------------------------------------------
CORS(app)

# --------------------------------------------------------------
# Simple rule‑based chatbot logic.
# --------------------------------------------------------------
# You can extend this dictionary with more patterns / answers.
RESPONSES: Dict[str, List[str]] = {
    "hello": [
        "Hey there! 👋 How can I help you today?",
        "Hi! What would you like to talk about?",
    ],
    "hi": [
        "Hello! 😊 Feel free to ask me anything.",
        "Hey! What’s on your mind?",
    ],
    "bye": [
        "Goodbye! 👋 Have a great day!",
        "See you later! Take care.",
    ],
    "thanks": [
        "You’re welcome! Glad I could help.",
        "Anytime! Let me know if you need anything else.",
    ],
    "joke": [
        "Why don’t scientists trust atoms? Because they make up everything! 😆",
        "I told my computer I needed a break, and it said ‘No problem – I’ll go to sleep.’ 😴",
    ],
    "help": [
        "I can chat about anything, tell jokes, or answer simple questions. Try saying “hello”, “joke”, or just ask me something.",
    ],
}


def chat(user_input: str) -> str:
    answer = asyncio.run(search_graph_and_format_results(user_input, usr_falkor_driver, usr_embed_client, usr_cross_encoder, usr_llm_client, usr_graphiti))
    print("answer")
    print(answer)
    answer_real = salvage_json(answer)
    answer_real = answer_real.get('answer', "Sorry, I couldn't find the information you requested.")

    # Fallback – echo the user's message (you can replace with more logic)
    return answer_real


# --------------------------------------------------------------
# Helper: log request/response with a timestamp
# --------------------------------------------------------------
def log(message: str) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] {message}")


# --------------------------------------------------------------
# API Endpoint – the one the front‑end will call
# --------------------------------------------------------------
@app.route("/chat", methods=["POST"])
def chat_endpoint():
    """
    Expected JSON payload:
    {
        "message": "your text"
    }

    Returns:
    {
        "response": "bot reply"
    }
    """
    # -----------------------------------------------------------------
    # 1️⃣ Parse JSON safely
    # -----------------------------------------------------------------
    data = request.get_json(silent=True)
    if not data:
        log("❌ Invalid JSON payload")
        return jsonify({"error": "Invalid JSON"}), 400

    user_msg = data.get("message", "").strip()
    if not user_msg:
        log("❌ Empty 'message' field")
        return jsonify({"error": "Missing 'message' field"}), 400

    # -----------------------------------------------------------------
    # 2️⃣ Simulate a "thinking" delay so the UI’s typing‑indicator shows
    # -----------------------------------------------------------------
    simulated_delay = random.uniform(0.4, 1.2)   # seconds
    time.sleep(simulated_delay)

    # -----------------------------------------------------------------
    # 3️⃣ Generate the reply
    # -----------------------------------------------------------------
    try:
        reply = chat(user_msg)
        log(f"🗣️  User: {user_msg} | Bot: {reply}")
        return jsonify({"response": reply})
    except Exception as exc:          # pragma: no cover
        # In a real service you would log the traceback.
        log(f"❗ Unexpected error: {exc}")
        return jsonify({"error": "Internal server error"}), 500


# --------------------------------------------------------------
# Health‑check endpoint (optional but handy)
# --------------------------------------------------------------
@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"status": "ok"}), 200


# --------------------------------------------------------------
# Run the app (development mode)
# --------------------------------------------------------------
if __name__ == "__main__":
    # Accessible from other devices on the same network:
    #   http://<your‑machine‑ip>:5000/
    app.run(host="0.0.0.0", port=5011, debug=True)