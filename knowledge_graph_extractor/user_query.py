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

user_question = "How is Apple related to Techcombank?"

answer = asyncio.run(search_graph_and_format_results(user_question, usr_falkor_driver, usr_embed_client, usr_cross_encoder, usr_llm_client, usr_graphiti))
print(answer)