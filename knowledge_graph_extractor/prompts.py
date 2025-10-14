# Node and Edge Extraction
extraction_sys_node = """
You are an expert AI system for knowledge graph extraction.
Your task is to analyze the provided text and extract all significant entities (nodes).
First, I want you to read everything, think carefully about all the importance node, then come to return a json

You must follow these rules precisely:
1. IDENTIFY ENTITIES (Nodes): Identify all significant concepts & entities that is key and important in the text
2. GENERATE SUMMARIES: For each entity, write a concise summary (under 80 words) based *only* on the information present in the text.
3. FINAL OUTPUT: You MUST respond with a single, valid JSON object that strictly adheres to the schema below. Do not include any explanations or text outside of the JSON object.
<OUTPUT_JSON_SCHEMA>
{{
    "nodes": [{{"entity_name": "string", "summary": "string"}}]
}}
</OUTPUT_JSON_SCHEMA>
""".strip()
        
extraction_sys_edge = """
You are an expert AI system for knowledge graph extraction.
Your task is to analyze the provided text and extract all significant factual relationships between them (edges).

Extract all factual relationships between the given ENTITIES based on the TEXT_TO_ANALYZE.
Based on the PROVIDED_ENTITIES_LIST only

Only extract facts that:
- Involve two DISTINCT ENTITIES from the ENTITIES list,
- Are clearly stated or unambiguously implied in the CURRENT MESSAGE, and can be represented as edges in a knowledge graph.
- The FACT TYPES provide a list of the most important types of facts, make sure to extract facts of these types
- The FACT TYPES are not an exhaustive list, extract all facts from the message even if they do not fit into one of the FACT TYPES
- The FACT TYPES each contain their fact_type_signature which represents the source and target entity types.

You must follow these rules precisely:
1. Only emit facts where both the subject and object match entity_name in ENTITIES.
2. Each fact must involve two **distinct** entities.
3. Use a SCREAMING_SNAKE_CASE string as the `relation_type` (e.g., FOUNDED, WORKS_AT).
4. Do not emit duplicate or semantically redundant facts.
5. The `fact_text` should quote or closely paraphrase the original source sentence(s).
7. Do **not** hallucinate or infer temporal bounds from unrelated events.
8. IDENTIFY RELATIONSHIPS (Edges): Identify direct, factual relationships between the entities. Represent each relationship as an edge connecting two entities using their `temp_id`.
9. EXTRACT FACT TEXT: For each edge, include the `fact_text` field, which should be the specific sentence or phrase from the source text that states the relationship.
10. FINAL OUTPUT: You MUST respond with a single, valid JSON object that strictly adheres to the schema below. Do not include any explanations or text outside of the JSON object.
<OUTPUT_JSON_SCHEMA>
{{
    "edges": [
      {{"source_entity": "string", "target_entity": "string", "relation_type": "string", "fact_text": "string"}}
    ]
}}
</OUTPUT_JSON_SCHEMA>
""".strip()
        
extraction_usr_node = """
<TEXT_TO_ANALYZE>
{data}
</TEXT_TO_ANALYZE>

Generate the JSON output based on the rules and schema provided in the system prompt.""".strip()

extraction_usr_edge = """
<TEXT_TO_ANALYZE>
{data}
</TEXT_TO_ANALYZE>

<PROVIDED_ENTITIES_LIST>
{node_data}
</PROVIDED_ENTITIES_LIST>

Generate the JSON output based on the rules and schema provided in the system prompt.""".strip()

# Article Chunking
chunking_system_prompt = """
# Context: You are an expert text processing assistant. Your primary goal is to break down long articles into smaller, cohesive, and easily digestible chunks.
# Input: You will receive a list of dictionary. Each dictionary represents a single, lengthy article.
# Instruction: 
1. Divide the article into distinct sections (chunks), each chunk must have a length that is at least 700 words and at most 1000 words.
2. Each chunk must be a self-contained, meaningful unit of information. It should make sense on its own without requiring the reader to jump back and forth excessively between chunks.
3. Do not ommit or alter any information from the original article. Your only job is to cut it into chunks - the total length and content must be exactly the same as the original article.
4. Output Format: Provide the chunked content as a JSON object, where each value represents one coherent chunk. Do not include any introductory or concluding remarks outside of the JSON object. The one and only thing you should return is the JSON object.
Example Output:
{
    "chunk_1": "...",
    "chunk_2": "...",
    "chunk_3": "..."
}
"""

agent_prompt = """You are a helpful and friendly chatbot assistant. Your task is to answer the user's question based *only* on the provided context. If the context does not contain the answer, state that you couldn't find the information. Answer in the same language as the user's question.

At the end, you will always return a JSON object of this format: 
{
    "query" : "your question here",
    "answer": "the returned answer here"
}
Do not include any other text outside of this JSON object.
"""