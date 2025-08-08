from pipeline import processing_node_edge
from input_text import text
import asyncio
from pipeline import advanced_deduplication_controller

# Changable text and database name
input = text
database = "aug-8-db-tech-doc"

# Add document to knowledge graph
asyncio.run(processing_node_edge(text, database))