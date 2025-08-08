import uuid
import asyncio
from typing import List
from .prompts import extraction_sys_edge, extraction_usr_edge, extraction_sys_node, extraction_usr_node, chunking_system_prompt
from .llm import llm_call, chunking_llm_call, salvage_json
from .graph_ops import add_metadata_to_nodes, add_metadata_to_edge, node_to_db, edge_to_db, episodic_generator, advanced_deduplication_controller
from .input_text import text 

async def each_ep_generator_node_edge(data, db_name, ep_name):
	#* Step 1: Generate Nodes
	node_step1 = salvage_json(llm_call(sys_prompt=extraction_sys_node,
	                       user_prompt=extraction_usr_node.format(data=data)))
 
	#* Step 2: Generate Edges
	edge_step1 = salvage_json(llm_call(sys_prompt=extraction_sys_edge,
	                       user_prompt=extraction_usr_edge.format(data=data, node_data=node_step1)))
   
	episode_uuid = str(uuid.uuid4())
			
	node_step2 = add_metadata_to_nodes(node_step1, 'Entity')
 
	await node_to_db(node_step2, db_name)
 
	edge_step2 = await add_metadata_to_edge(edge_step1, 'RELATES_TO', db_name, episode_uuid)
 
	await edge_to_db(edge_step2, db_name)
 
	episode_node, episode_edges = episodic_generator(node_step2, edge_step2, ep_name, data, 'text_source', episode_uuid)
 
	await node_to_db(episode_node, db_name)

	await edge_to_db(episode_edges, db_name)

	await advanced_deduplication_controller(db_name, 0.88)
 
	return "DONE"

async def processing_node_edge(text: list, db_name: str):
    for i in range(0, len(text)):
    
        print(f"\n\n--- Start processing article_{i} ---")
        print("STEP 1: Chunking article content...")
        article_content = text[i][f"article_{i}"]
        chunked_article = chunking_llm_call(article_content, chunking_system_prompt)

        print("STEP 2: Processing nodes and edges...")
        for j, chunk in enumerate(chunked_article.values(), start=0):
            await each_ep_generator_node_edge(chunk.strip(), db_name, f"chunk_{j}_article_{i}")
            await advanced_deduplication_controller(db_name, 0.88)
            print(f"Processed chunk {j} for article_{i}")
        
        print(f"--- Finish parsing article_{i} ---")
        print("Waiting 1 second to respect rate limits...\n")
        await asyncio.sleep(20)



async def process_articles(text: list, db_name: str):
    for i in range(len(text)):

        print(f"\n\n--- Start processing article_{i} ---")
        print("STEP 1: Chunking article content...")
        article_content = text[i][f"article_{i}"]
        chunked_article = chunking_llm_call(article_content, chunking_system_prompt)

        print("STEP 2: Extracting nodes and edges from chunks...")
        for j, chunk in enumerate(chunked_article.values()):
            data = chunk.strip()

            # Step 1: Generate Nodes
            node_step1 = salvage_json(
                llm_call(
                    sys_prompt=extraction_sys_node,
                    user_prompt=extraction_usr_node.format(data=data)
                )
            )

            # Step 2: Generate Edges
            edge_step1 = salvage_json(
                llm_call(
                    sys_prompt=extraction_sys_edge,
                    user_prompt=extraction_usr_edge.format(data=data, node_data=node_step1)
                )
            )

            # Step 3: Add metadata and store in DB
            episode_uuid = str(uuid.uuid4())
            node_step2 = add_metadata_to_nodes(node_step1, 'Entity')
            await node_to_db(node_step2, db_name)

            edge_step2 = await add_metadata_to_edge(edge_step1, 'RELATES_TO', db_name, episode_uuid)
            await edge_to_db(edge_step2, db_name)

            # Step 4: Create episodic node & edges
            episode_node, episode_edges = episodic_generator(
                node_step2,
                edge_step2,
                f"chunk_{j}_article_{i}",
                data,
                'text_source',
                episode_uuid
            )

            await node_to_db(episode_node, db_name)
            await edge_to_db(episode_edges, db_name)

            # Step 5: Deduplication
            await advanced_deduplication_controller(db_name, 0.88)

            print(f"Processed chunk {j} for article_{i}")

        print(f"--- Finish parsing article_{i} ---")
        print("Waiting 20 seconds to respect rate limits...\n")
        await asyncio.sleep(20)