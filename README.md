# Knowledge Graph Extraction System

A powerful knowledge graph extraction system that uses Google's Gemini AI models to extract entities and relationships from text documents and stores them in a FalkorDB graph database.

## Features

- **Intelligent Text Processing**: Automatically chunks large documents for optimal processing
- **Entity & Relationship Extraction**: Uses advanced LLM prompts to identify nodes and edges
- **Smart Deduplication**: Advanced similarity-based deduplication for both nodes and edges
- **Vector Embeddings**: Stores semantic embeddings for similarity search
- **Episodic Knowledge**: Links extracted facts back to their source documents
- **Scalable Architecture**: Async processing with rate limiting for API calls

## Architecture

The system processes documents through several stages:
1. **Chunking**: Large texts are broken into manageable chunks (700-1000 words)
2. **Entity Extraction**: Identifies key entities (nodes) from each chunk
3. **Relationship Extraction**: Finds factual relationships (edges) between entities
4. **Storage**: Saves nodes and edges to FalkorDB with metadata
5. **Deduplication**: Merges similar entities and consolidates duplicate relationships
6. **Episodic Linking**: Creates episodic nodes linking facts to source chunks

## Setup

### Prerequisites

- Python 3.8+
- FalkorDB (Redis with graph capabilities)
- Google Gemini API key

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv graphiti-env
source graphiti-env/bin/activate  # On Windows: graphiti-env\Scripts\activate

# Install required packages
pip install falkordb
pip install google-genai
pip install python-dotenv
pip install asyncio
pip install uuid
```

### 2. Set Up FalkorDB

#### Option A: Using Docker (Recommended)
```bash
# Pull and run FalkorDB
docker pull falkordb/falkordb:latest
docker run -p 6379:6379 falkordb/falkordb:latest
```

#### Option B: Local Installation
Follow the [FalkorDB installation guide](https://docs.falkordb.com/installation.html) for your operating system.

### 3. Configure Environment Variables

Create a `.env` file in your project root:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

To get a Gemini API key:
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy the key to your `.env` file

### 4. Verify Setup

Test your FalkorDB connection:
```bash
# Test Redis connection
redis-cli -p 6379 ping
# Should return: PONG
```

Test your API key by running a simple script:
```python
from dotenv import load_dotenv
import os
from google import genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)
print("✅ API key is working!")
```

## Document Ingestion

### 1. Prepare Your Documents

Add your text content to `kg_extractor/input_text.py`:

```python
# kg_extractor/input_text.py
text = [
    {
        "article_0": "Your first document content here..."
    },
    {
        "article_1": "Your second document content here..."
    }
    # Add more articles as needed
]
```

### 2. Configure Database Name

In `kg_extractor/main.py`, set your database name:

```python
database = "your_database_name"  # Change this to your preferred name
```

### 3. Run the Ingestion Process

```bash
# Navigate to the kg_extractor directory
cd kg_extractor

# Run the main ingestion script
python main.py
```

### Ingestion Process Overview

The system will:
1. **Chunk documents** into optimal sizes (700-1000 words)
2. **Extract entities** using specialized prompts
3. **Extract relationships** between identified entities
4. **Store in database** with embeddings and metadata
5. **Create episodic links** connecting facts to source chunks
6. **Deduplicate** similar entities and relationships
7. **Rate limit** API calls to respect service limits

### Expected Output

```
--- Start processing article_0 ---
STEP 1: Chunking article content...
STEP 2: Processing nodes and edges...
Processed chunk 0 for article_0
Processed chunk 1 for article_0
--- Finish parsing article_0 ---
===== Starting Advanced Deduplication and Consolidation Process =====
```

## Querying the Knowledge Graph

### Method 1: Using the Query Script

Create a query script similar to the one in your project:

```python
# query.py
import asyncio
from graphiti_core import Graphiti
from graphiti_core.driver.falkordb_driver import FalkorDriver
from graphiti_core.search.search_config_recipes import COMBINED_HYBRID_SEARCH_RRF
# ... other imports from your config

async def search_graph(query_text, db_name="your_database_name"):
    # Initialize your Graphiti instance (copy from your existing code)
    
    # Configure search
    search_config = COMBINED_HYBRID_SEARCH_RRF.model_copy(deep=True)
    search_config.limit = 10
    
    # Execute search
    results = await graphiti._search(
        query=query_text,
        config=search_config,
    )
    
    # Format results
    for node in results.nodes:
        print(f"Entity: {node.name}")
        print(f"Summary: {node.summary}\n")
    
    for edge in results.edges:
        print(f"Relationship: {edge.name}")
        print(f"Fact: {edge.fact}\n")

# Usage
query = "How much does Techcombank plan to invest in technology?"
asyncio.run(search_graph(query))
```

### Method 2: Direct Cypher Queries

Connect directly to FalkorDB and run Cypher queries:

```python
from falkordb.asyncio import FalkorDB
import asyncio

async def run_cypher_query(query, db_name="your_database_name"):
    client = FalkorDB(host="localhost", port=6379)
    graph = client.select_graph(db_name)
    
    result = await graph.query(query)
    
    for record in result.result_set:
        print(record)

# Example queries
queries = [
    # Find all entities
    "MATCH (n:Entity) RETURN n.name, n.summary LIMIT 10",
    
    # Find relationships
    "MATCH (a:Entity)-[r:RELATES_TO]->(b:Entity) RETURN a.name, r.fact, b.name LIMIT 10",
    
    # Find entities related to a topic
    "MATCH (n:Entity) WHERE n.name CONTAINS 'Techcombank' RETURN n.name, n.summary",
    
    # Find episodic content
    "MATCH (e:Episodic) RETURN e.name, e.content LIMIT 5"
]

for query in queries:
    print(f"\n--- Query: {query} ---")
    asyncio.run(run_cypher_query(query))
```

### Method 3: Semantic Search

Use vector similarity for semantic queries:

```python
async def semantic_search(query_text, db_name="your_database_name", limit=5):
    # Generate embedding for query
    from kg_extractor.llm import generate_embedding
    query_embedding = generate_embedding(query_text)
    
    # Find similar entities
    cypher = f"""
    MATCH (n:Entity)
    WHERE n.name_embedding IS NOT NULL
    WITH n, (2 - vec.cosineDistance(n.name_embedding, vecf32({query_embedding})))/2 AS similarity
    WHERE similarity > 0.7
    RETURN n.name, n.summary, similarity
    ORDER BY similarity DESC
    LIMIT {limit}
    """
    
    await run_cypher_query(cypher, db_name)

# Usage
asyncio.run(semantic_search("investment technology digital transformation"))
```

## Database Schema

### Node Types

- **Entity**: Main entities extracted from text
  - `name`: Entity name
  - `summary`: Entity description
  - `uuid`: Unique identifier
  - `name_embedding`: Vector embedding for similarity search
  - `created_at`: Timestamp

- **Episodic**: Source chunks and metadata
  - `name`: Chunk identifier
  - `content`: Original text content
  - `source`: Source type (e.g., "text")
  - `entity_edges`: Connected relationship IDs

### Relationship Types

- **RELATES_TO**: Factual relationships between entities
  - `fact`: Original text stating the relationship
  - `fact_embedding`: Vector embedding of the fact
  - `episodes`: List of episodic UUIDs where this fact appears

- **MENTIONS**: Links episodic nodes to mentioned entities

## Configuration

Key configuration options in `kg_extractor/config.py`:

```python
# Database connection
db_client = FalkorDB(
    host="localhost",     # Change if using remote FalkorDB
    port=6379,           # Default FalkorDB port
    username=None,       # Set if authentication required
    password=None,       # Set if authentication required
)

# API settings are in the LLM client configurations
```

## Troubleshooting

### Common Issues

1. **Empty output files**: Check file paths and permissions
2. **API rate limits**: Increase sleep times in the pipeline
3. **Database connection errors**: Verify FalkorDB is running on port 6379
4. **Memory issues**: Process smaller document chunks or reduce embedding dimensions

### Debug Mode

Add debug prints to track processing:

```python
print(f"Processing document: {article_content[:100]}...")  # First 100 chars
print(f"Extracted {len(nodes)} nodes and {len(edges)} edges")
```

### Logs

Monitor the output for:
- ✅ Successful processing messages
- ⚠️ Warning messages about skipped content
- ❌ Error messages requiring attention

## Performance Tips

1. **Batch Processing**: Process multiple documents in batches
2. **Concurrent Processing**: Use asyncio for I/O operations
3. **Embedding Caching**: Cache embeddings for repeated queries  
4. **Database Indexing**: Create indexes on frequently queried properties
5. **Rate Limiting**: Respect API limits to avoid throttling

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.