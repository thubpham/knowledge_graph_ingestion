import re
import json
import time
import asyncio
from functools import wraps
from google.genai import types
from google.genai.errors import ClientError
from .config import ai_client


def salvage_json(raw_output):
	if not raw_output:
		return None

	raw_output = re.sub(r"^```json|^```|```$", "", raw_output.strip(), flags=re.MULTILINE).strip()

	try:
		return json.loads(raw_output)
	except json.JSONDecodeError:
		print("Warning: Initial JSON parse failed, attempting salvage.")
		match = re.search(r"\{.*\}", raw_output, re.DOTALL)
		if match:
			try:
				return json.loads(match.group(0))
			except json.JSONDecodeError:
				print("Error: Could not parse JSON after salvage.")
				raise

def generate_embedding(input_data):
    time.sleep(0.3)
    result = ai_client.models.embed_content(
        model="gemini-embedding-001",
        contents=[input_data],
        config=types.EmbedContentConfig(output_dimensionality=1024),
    )
    if not result.embeddings or not result.embeddings[0].values:
        raise ValueError('No embeddings returned from Gemini API in create()')

    return result.embeddings[0].values

def llm_call(user_prompt, sys_prompt):
	res = ai_client.models.generate_content(
		model="gemini-2.5-flash-lite",
		config=types.GenerateContentConfig(
			thinking_config=types.ThinkingConfig(
				thinking_budget=2048,
				include_thoughts=False
			),
			system_instruction=sys_prompt,
			temperature=0.3,
			response_mime_type='application/json',
			top_p=0.9,
			max_output_tokens=60000,
		),
		contents=user_prompt
	)
	return res.text

def chunking_llm_call(input_text, sys_prompt):
	words = input_text.split()

	if len(words) <= 3000:
		print("Input is within the word limit. No chunking needed.")
		return {"chunk_1": input_text}

	try:
		print("Input is longer than 3000 words. Chunking...")
		user_prompt = f"""Below is the article to be processed:\n{input_text}"""

		res = ai_client.models.generate_content(
			model="gemini-2.5-flash",
			config=types.GenerateContentConfig(
				system_instruction=sys_prompt,
				temperature=0.1,
				response_mime_type='application/json',
				top_p=0.9,
				max_output_tokens=60000,
			),
			contents=user_prompt
		)

		raw_output = res.text
		json_output = salvage_json(raw_output)
		print("Chunking completed. Waiting 30 seconds to respect rate limits...\n")
		time.sleep(30)
		return json_output

	except Exception as e:
		print(f"An error occurred during chunking: {e}")
		return {"error": str(e)}
