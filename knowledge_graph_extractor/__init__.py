import asyncio
from .pipeline import processing_node_edge

def extract_knowledge_graph(text, db_name):
	"""
	Main API function to extract a knowledge graph from text and store it in the database.
	Args:
		text (list): List of dicts, each containing an article or document.
		db_name (str): Name of the database to store the graph.
	Returns:
		None
	"""
	asyncio.run(processing_node_edge(text, db_name))
