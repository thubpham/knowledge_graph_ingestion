# ============================================
# 🚀 Knowledge Graph Ingestion Script
# ============================================
# This script adds a document (input text) into a knowledge graph database
# by calling the `processing_node_edge()` function from the pipeline module.
#
# 👉 To use this script:
#    1. Update the `text` content (either directly in input_text.py or here).
#    2. Set your desired database name in `database`.
#    3. Run this script with:
#         python -m knowledge_graph_extractor.kg_extractor.main
#
# ============================================

from knowledge_graph_extractor.pipeline import processing_node_edge 
from knowledge_graph_extractor.input_text import text
import asyncio

# --------------------------------------------
# STEP 1: Define input and database name
# --------------------------------------------
# The text to be processed can come from:
# - input_text.py (default import)
# - or directly pasted here for one-off runs.

input = text
database = "aug-8-db-tech-doc"

# --------------------------------------------
# STEP 2: Process the document
# --------------------------------------------
# This calls the async pipeline function that:
# - Extracts entities and relationships from the text
# - Cleans and deduplicates data
# - Adds nodes and edges into your knowledge graph database

asyncio.run(processing_node_edge(text, database))