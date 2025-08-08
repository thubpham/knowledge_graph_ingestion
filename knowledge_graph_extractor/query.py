import os
import json
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
from kg_extractor.llm import llm_call, salvage_json
from kg_extractor.prompts import agent_prompt

async def search_graph_and_format_results(query_from_user, falkor_driver, embed_client, cross_encoder, llm_client, graphiti) -> str:
	class NodeResult:
		def __init__(self, name, summary, uuid=None):
			self.name = name
			self.summary = summary
			self.uuid = uuid

	async def get_node_from_uuid(uuid):
		query = """MATCH (n:Entity {uuid: '""" + uuid + """'})
				RETURN
					n.name AS name,
					n.summary AS summary,
					n.uuid AS uuid
				"""
		res = await falkor_driver.execute_query(query)
		if res and res[0]:
			data = res[0][0]
			# Check if the returned data is a dictionary and adapt
			if isinstance(data, dict):
				return NodeResult(data.get('name'), data.get('summary'), data.get('uuid'))
			# If it's already an object with the expected attributes, return it directly
			elif hasattr(data, 'name') and hasattr(data, 'summary'):
				return data
		return None 

	node_search_config = COMBINED_HYBRID_SEARCH_RRF.model_copy(deep=True)
	node_search_config.limit = 5  # Limit to 5 results

	# Execute the node search
	node_search_results = await graphiti._search(
		query=query_from_user,
		config=node_search_config,
	)

	output_string = ""
	nodes = node_search_results.nodes
	edges = node_search_results.edges

	for node, edge in itertools.zip_longest(nodes, edges, fillvalue=None):
		# Process node if it exists for the current iteration
		if node is not None:
			output_string += f"SOURCE Node Name: {node.name}\n"
			output_string += f"SOURCE Node Summary: {node.summary}\n"

		# Process edge if it exists for the current iteration
		if edge is not None:
			target_node = await get_node_from_uuid(edge.target_node_uuid)

			source_node_name = node.name if node is not None else "Unknown Source Node (pairing mismatch)"
			
			# Safely get target node name and summary, in case target_node was not found.
			target_node_name = target_node.name if target_node is not None else "Unknown Target Node (UUID not found)"
			target_node_summary = target_node.summary if target_node is not None else "N/A"

			output_string += f"TARGET Node Name: {target_node_name}\n"
			output_string += f"TARGET Node Summary: {target_node_summary}\n\n"
			output_string += f"## Relationship\n"
			output_string += f"{source_node_name} -[:{edge.name}]-> {target_node_name} (FACT:{edge.fact})\n"
			output_string += f"------\n"
	
	systemp_prompt = f"""
	System Prompt:
	{agent_prompt}
	
	Queried context: 
	{output_string}
	"""

	response = llm_call(
		user_prompt=query_from_user,
		sys_prompt=systemp_prompt
	)

	json_response = salvage_json(response)

	return json_response