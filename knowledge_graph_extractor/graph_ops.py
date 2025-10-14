import uuid
import json
from datetime import datetime, timedelta, timezone
from .llm import generate_embedding, salvage_json, llm_call
from .db import execute_query, get_uuid_from_name
from typing import List, Dict, Any
from collections import defaultdict
import asyncio

# Add Metadata to Node and Edge
def add_metadata_to_nodes(json_data, label):
	if label not in ["Entity", "Episodic"]:
		raise ValueError("The label must be either 'Entity' or 'Episodic'.")

	if "nodes" not in json_data or not isinstance(json_data["nodes"], list):
		raise ValueError("The input JSON must contain a key 'nodes' with a list of edge objects.")

	updated_json_data = json_data.copy()
	nodes = updated_json_data.get("nodes", [])
	
	for node in nodes:
		if "entity_name" in node:
			node["name"] = node.pop("entity_name")
		node["uuid"] = str(uuid.uuid4())
		node["name_embedding"] = generate_embedding(str(node["name"]))
		node["created_at"] = datetime.now(tz=timezone(timedelta(hours=7))).isoformat()
		node["labels"] = label
		node["group_id"] = '_'
	
	return updated_json_data

async def add_metadata_to_edge(json_data, label, db_name, episode_uuid):
	if label not in ["MENTIONS", "RELATES_TO"]:
		raise ValueError("The label must be either 'MENTIONS' or 'RELATES_TO'.")

	if "edges" not in json_data or not isinstance(json_data["edges"], list):
		raise ValueError("The input JSON must contain a key 'edges' with a list of edge objects.")

	updated_json_data = {k: v[:] if isinstance(v, list) else v for k, v in json_data.items()}
  
	transformed_edges = []
	for edge in updated_json_data.get("edges", []):

		transformed_edge = {
		"uuid": str(uuid.uuid4()),
		"source_entity": await get_uuid_from_name(edge.get("source_entity"), db_name),
		"target_entity": await get_uuid_from_name(edge.get("target_entity"), db_name),
		"name": edge.get("relation_type"),
		"created_at": datetime.now(tz=timezone(timedelta(hours=7))).isoformat(),
		"group_id": "_",
		"labels": label,
		"episodes": [episode_uuid],
		"fact": edge.get("fact_text"),
		"fact_embedding": generate_embedding(edge.get("fact_text"))
		}
		transformed_edges.append(transformed_edge)
  
	updated_json_data["edges"] = transformed_edges
	
	return updated_json_data

def episodic_generator(node_json, edge_json, episodic_name, data, source_description, episode_uuid):
	
	edges_of_episode = []
	entity_edges = []
		
	for each in edge_json['edges']:
		entity_edges.append(each['uuid'])
	
	episode_node = {
		"uuid": episode_uuid,
  		"group_id": "_",
		"source_description": source_description,
		"source" : "text",
		"content": data,
		"labels": "Episodic",
		"entity_edges": entity_edges,
		"name": episodic_name,
		"created_at": datetime.now(tz=timezone(timedelta(hours=7))).isoformat(),
 		"valid_at":datetime.now(tz=timezone(timedelta(hours=7))).isoformat(),}
	
	for each in node_json['nodes']:
		episode_edge = {
			"uuid": str(uuid.uuid4()),
			"group_id": "_",
			"created_at": datetime.now(tz=timezone(timedelta(hours=7))).isoformat(),
			"labels": 'MENTIONS',
			"target_entity": each['uuid'],
			"source_entity": episode_uuid
		}
		edges_of_episode.append(episode_edge)

	final_episode_node = {"nodes": [episode_node]}
	final_episode_edges = {"edges": edges_of_episode}

	return final_episode_node, final_episode_edges


async def node_to_db(data, db_name):
	nodes = data.get('nodes')
	for node in nodes:
		node_labels = node['labels']
		properties = {key: value for key, value in node.items() if key != 'labels'}
		prop_list = []
		for key, value in properties.items():
			if key == 'name_embedding':
				prop_list.append(f"{key}: vecf32({value})")
			else:
				prop_list.append(f"{key}: {json.dumps(value)}")
		props_string = ", ".join(prop_list)
		query = f"CREATE (n:{node_labels} {{{props_string}}})"
		await execute_query(query, db_name)
  
async def edge_to_db(data, db_name):
	edges = data.get('edges')
	for edge in edges:
		source_uuid = edge.get('source_entity')
		target_uuid = edge.get('target_entity')
		relationship_type = edge.get('labels', 'RELATES_TO') # Default to RELATES_TO if not present

		# Proceed only if source and target UUIDs are present
		if source_uuid and target_uuid:
			# Create a dictionary of properties for the edge, excluding keys used for matching/typing
			edge_props_dict = {
				k: v for k, v in edge.items() 
				if k not in ['source_entity', 'target_entity', 'labels']
			}

			prop_list = []
			for key, value in edge_props_dict.items():
				# Check if the value is a list (assumed to be a vector for embedding)
				if key == 'fact_embedding':
					prop_list.append(f"{key}: vecf32({value})")
				else:
					# Use json.dumps for all other types for safe string formatting
					prop_list.append(f"{key}: {json.dumps(value)}")

			edge_props_str = ", ".join(prop_list)

			query = f"""
		MATCH (a), (b)
		WHERE a.uuid = {json.dumps(source_uuid)} AND b.uuid = {json.dumps(target_uuid)}
		CREATE (a)-[r:{relationship_type} {{{edge_props_str}}}]->(b)
		""".strip()
			await execute_query(query, db_name)


from typing import List, Dict, Any
from collections import defaultdict

async def find_duplicate_communities(db_name: str, similarity_threshold: float = 0.91):
	"""
	Finds communities of duplicate nodes using real vector similarity search.

	It fetches all pairs of nodes whose 'name_embedding' are closer than the
	threshold, then uses a client-side graph traversal to group these pairs
	into distinct communities of duplicates.

	Args:
		db_name: The name of the database.
		similarity_threshold: The cosine similarity score (0.0 to 1.0) above which
							  nodes are considered duplicates.

	Returns:
		A list of lists, where each inner list contains the UUIDs of a duplicate community.
	"""
	print(f"\n--- Step 4.1: Finding Duplicate Communities (Threshold > {similarity_threshold}) ---")
	
	query = """
	MATCH (n1:Entity), (n2:Entity)
	WHERE id(n1) < id(n2)
	WITH n1, n2, (2 - vec.cosineDistance(n1.name_embedding, n2.name_embedding))/2 AS similarity
	WHERE similarity > $threshold
	RETURN n1.uuid AS uuid1, n2.uuid AS uuid2
	"""
	
	result = await execute_query(query, db_name, threshold=similarity_threshold)

	if not result:
		print("No similar pairs found. The graph appears clean.")
		return []

	print(f"Found {len(result)} similar pairs. Building communities...")

	# Use a graph traversal algorithm (BFS/DFS) to find connected components (communities)
	adj = defaultdict(list)
	nodes_in_pairs = set()
	for record in result:
		u, v = record["uuid1"], record["uuid2"]
		adj[u].append(v)
		adj[v].append(u)
		nodes_in_pairs.add(u)
		nodes_in_pairs.add(v)

	communities = []
	visited = set()
	for node_uuid in nodes_in_pairs:
		if node_uuid not in visited:
			community = []
			q = [node_uuid]
			visited.add(node_uuid)
			head = 0
			while head < len(q):
				current_node = q[head]
				head += 1
				community.append(current_node)
				for neighbor in adj[current_node]:
					if neighbor not in visited:
						visited.add(neighbor)
						q.append(neighbor)
			communities.append(community)

	print(f"Grouped pairs into {len(communities)} distinct duplicate communities.")
	return communities


async def select_canonical_node(db_name: str, community_uuids: List[str]) -> str:
	"""
	Selects the best node from a community to be the canonical (surviving) node.
	It scores nodes based on relationship count (degree) and property completeness,
	using the creation date as a tie-breaker.

	Args:
		db_name: The name of the database.
		community_uuids: A list of UUIDs in the duplicate community.

	Returns:
		The UUID of the selected canonical node.
	"""
	print(f"  - Selecting canonical node from community of size {len(community_uuids)}...")
	
	# This query fetches metrics for each node in the community to calculate a "survivor score".
	# Degree (relationship count) is a great proxy for importance.
	query = """
	UNWIND $uuids AS uuid
	MATCH (n:Entity {uuid: uuid})
	OPTIONAL MATCH (n)-[r]-()
	WITH n, count(r) AS degree
	RETURN n.uuid AS uuid,
		   n.created_at AS created_at,
		   size(n.summary) AS summary_length,
		   degree
	"""
	
	results = await execute_query(query, db_name, uuids=community_uuids)
	
	if not results:
		raise ValueError(f"Query for community {community_uuids} returned no results.")
	
	best_node_uuid = None
	max_score = -1.0
	best_created_at = datetime.max
	
	WEIGHTS = {
		'degree': 10.0,           # Each relationship is highly valuable.
		'summary_length': 0.08,   # Each character in the summary adds a small amount to the score.
	}

	for record in results:
		degree_score = record["degree"] * WEIGHTS['degree']
		summary_score = (record["summary_length"] or 0) * WEIGHTS['summary_length']

		# The total score is the sum of all weighted components
		score = degree_score + summary_score

		uuid = record["uuid"]
		created_at = record["created_at"]

		# Tie-breaking logic:
		# 1. Higher score wins.
		# 2. If scores are identical, the older node (earlier created_at) wins.
		if score > max_score or (score == max_score and created_at < best_created_at):
			max_score = score
			best_node_uuid = uuid
			best_created_at = created_at

	return best_node_uuid

async def find_similar_edge_communities(db_name: str, canonical_uuid: str, similarity_threshold: float = 0.88) -> List[List[int]]:
	"""
	Finds communities of semantically similar edges for a given node.
	
	This function fetches all outgoing edges from the canonical node, compares their
	`fact_embedding` property, and groups highly similar edges into communities.

	Args:
		db_name: The name of the database.
		canonical_uuid: The UUID of the node whose edges are to be deduplicated.
		similarity_threshold: The cosine similarity score above which edges are considered duplicates.

	Returns:
		A list of lists, where each inner list contains the database IDs of a duplicate edge community.
	"""
	print(f"  - Finding similar edge communities for node {canonical_uuid[:8]} (Threshold > {similarity_threshold})...")
	
	# This query finds pairs of similar outgoing edges from the canonical node.
	query = """
	MATCH (canonical:Entity {uuid: $uuid})-[r1]->()
	MATCH (canonical)-[r2]->()
	WHERE id(r1) < id(r2) AND r1.fact_embedding IS NOT NULL AND r2.fact_embedding IS NOT NULL

	WITH r1, r2, (2 - vec.cosineDistance(r1.fact_embedding, r2.fact_embedding))/2 AS similarity
	WHERE similarity > $threshold

	RETURN id(r1) AS id1, id(r2) AS id2
	"""
	
	results = await execute_query(query, database=db_name, uuid=canonical_uuid, threshold=similarity_threshold)

	if not results:
		print("    - No similar edge pairs found.")
		return []

	print(f"    - Found {len(results)} similar edge pairs. Building communities...")

	# Build communities from pairs using a graph traversal (same logic as for nodes)
	adj = defaultdict(list)
	edges_in_pairs = set()
	for record in results:
		u, v = record["id1"], record["id2"]
		adj[u].append(v)
		adj[v].append(u)
		edges_in_pairs.add(u)
		edges_in_pairs.add(v)

	communities = []
	visited = set()
	for edge_id in edges_in_pairs:
		if edge_id not in visited:
			community = []
			q = [edge_id]
			visited.add(edge_id)
			head = 0
			while head < len(q):
				current_edge = q[head]
				head += 1
				community.append(current_edge)
				for neighbor in adj[current_edge]:
					if neighbor not in visited:
						visited.add(neighbor)
						q.append(neighbor)
			communities.append(community)

	print(f"    - Grouped into {len(communities)} distinct duplicate edge communities.")
	return communities

async def merge_edge_community(db_name: str, edge_community_ids: List[int]):
	"""
	Merges a community of duplicate edges into a single, summarized edge.
	"""
	if len(edge_community_ids) < 2:
		return

	print(f"    - Merging edge community of size {len(edge_community_ids)}...")

	# 1. Fetch data for all edges in the community
	query_fetch_edges = """
	UNWIND $ids AS edge_id
	MATCH ()-[r]-() WHERE id(r) = edge_id
	RETURN id(r) AS id, r.fact AS fact, r.episodes AS episodes, r.created_at AS created_at
	ORDER BY r.created_at ASC
	"""
	edge_data_list = await execute_query(query_fetch_edges, database=db_name, ids=edge_community_ids)

	if not edge_data_list:
		print("      - Warning: Could not fetch data for edge community. Skipping.")
		return
		
	# 2. Select canonical edge (the oldest), and gather data for merge
	canonical_edge = edge_data_list[0]
	canonical_edge_id = canonical_edge['id']
	duplicate_edge_ids = [edge['id'] for edge in edge_data_list[1:]]

	facts_to_merge = [edge['fact'] for edge in edge_data_list if edge.get('fact')]
	
	# 3. Use LLM to synthesize a new, better fact
	synthesized_fact = canonical_edge.get('fact', '')
	if len(facts_to_merge) > 1:
		print("      - Synthesizing new edge fact with LLM...")
		try:
			llm_response = salvage_json(llm_call(
				sys_prompt="You are an expert graph data analyst. Your task is to merge multiple 'fact' descriptions from duplicate relationships into one definitive, consolidated sentence.",
				user_prompt=f"""The following facts all describe a similar relationship. Please merge them into concise, comprehensive, and clear short paragraph, retain all the key point and facts.
FACTS TO MERGE:
- {" - ".join(facts_to_merge)}

Return a JSON object with a single key: "synthesized_fact".
"""
			))
			if llm_response and 'synthesized_fact' in llm_response:
				synthesized_fact = llm_response['synthesized_fact']
				print("      - LLM synthesis of fact successful.")
		except Exception as e:
			print(f"      - LLM synthesis failed, will use fact from the oldest edge. Error: {e}")
			
	# 4. Generate new embedding and merge properties
	new_embedding = generate_embedding(synthesized_fact)
	embedding_str = str(new_embedding)[1:-1]
	
	# Merge 'episodes' by creating a unique set
	all_episodes = set()
	for edge in edge_data_list:
		if edge.get('episodes'):
			all_episodes.update(edge['episodes'])
	merged_episodes = list(all_episodes)

	# 5. Perform the merge and delete in a single transaction
	try:
		# First, verify the canonical edge still exists
		verify_query = """
		MATCH ()-[r]-() WHERE id(r) = $canonical_id
		RETURN count(r) as exists
		"""
		verify_result = await execute_query(verify_query, db_name, canonical_id=canonical_edge_id)
		
		if not verify_result or verify_result[0]['exists'] == 0:
			print(f"      - Warning: Canonical edge {canonical_edge_id} no longer exists")
			return

		# Update canonical edge
		query_update = f"""
		MATCH ()-[r]-() WHERE id(r) = $canonical_id
		SET r.fact = $new_fact,
			r.fact_embedding = vecf32([{embedding_str}]),
			r.episodes = $merged_episodes,
			r.updated_at = $now
		RETURN count(r) as updated
		"""
		
		update_result = await execute_query(query_update, db_name, 
										  canonical_id=canonical_edge_id,
										  new_fact=synthesized_fact,
										  merged_episodes=merged_episodes,
										  now=datetime.now(tz=timezone(timedelta(hours=7))).isoformat())
		
		if not update_result or update_result[0]['updated'] == 0:
			print(f"      - Warning: Failed to update canonical edge {canonical_edge_id}")
			return

		# Delete duplicate edges one by one with validation
		deleted_count = 0
		for dup_id in duplicate_edge_ids:
			try:
				delete_query = """
				MATCH ()-[r]-() WHERE id(r) = $edge_id
				DELETE r
				RETURN count(r) as deleted
				"""
				delete_result = await execute_query(delete_query, db_name, edge_id=dup_id)
				if delete_result and delete_result[0]['deleted'] > 0:
					deleted_count += 1
			except Exception as e:
				print(f"      - Warning: Could not delete edge {dup_id}: {e}")
		
		print(f"      - Updated 1 canonical edge, deleted {deleted_count} duplicate edges.")
		
	except Exception as e:
		print(f"      - Error during edge merge transaction: {e}")
		return


async def consolidate_edges_for_node(db_name: str, canonical_uuid: str):
	"""
	Orchestrates the new, advanced edge deduplication process for a single node.
	"""
	print(f"\n--- Step 4.4: Consolidating Edges for Node {canonical_uuid[:8]} ---")
	
	# Find communities of similar edges based on 'fact' similarity
	edge_communities = await find_similar_edge_communities(db_name, canonical_uuid)
	
	if not edge_communities:
		print("  - No semantic edge duplications found. Node is clean.")
		return
		
	# Merge each community into a single, summarized edge
	for community in edge_communities:
		await merge_edge_community(db_name, community)


async def merge_and_consolidate_nodes(db_name: str, canonical_uuid: str, duplicate_uuids: List[str]):
	"""
	Merges duplicate nodes into the canonical node, re-wires relationships,
	and then triggers the advanced edge consolidation.
	"""
	print(f"\n--- Step 4.3: Merging {len(duplicate_uuids)} nodes into {canonical_uuid[:8]} ---")
	
	# 1. Fetch node data for property merge
	query_fetch_data = "MATCH (n:Entity) WHERE n.uuid IN $uuids RETURN n.uuid AS uuid, n.summary AS summary, n.name AS name"
	all_uuids = [canonical_uuid] + duplicate_uuids
	print(all_uuids)
	results = await execute_query(query_fetch_data, database=db_name, uuids=all_uuids)
	node_data = {record["uuid"]: {"summary": record.get("summary"), "name": record.get("name")} for record in results}

	# 2. Use LLM to synthesize a new summary
	summaries_to_merge = [data['summary'] for data in node_data.values() if data and data.get('summary')]
	final_summary = node_data.get(canonical_uuid, {}).get('summary', '')

	if len(summaries_to_merge) > 1:
		print("  - Synthesizing new node summary with LLM...")
		try:
			llm_response = salvage_json(llm_call(
				sys_prompt="You are an expert knowledge graph editor. Your task is to synthesize multiple descriptions of the same entity into one definitive, high-quality summary.",
				user_prompt=f"""The following summaries all describe the entity '{node_data[canonical_uuid]['name']}'.  Please merge them into concise, comprehensive, clear, and factually accurate summary short. retain all the key point and facts.

SUMMARIES TO MERGE:
- {" - ".join(summaries_to_merge)}

Return a JSON object with a single key: "synthesized_summary".
"""
			))
			if llm_response and 'synthesized_summary' in llm_response:
				final_summary = llm_response['synthesized_summary']
				print("  - LLM synthesis successful.")
		except Exception as e:
			print(f"  - LLM synthesis failed, will use canonical's summary. Error: {e}")
			
	final_embedding = generate_embedding(final_summary)
	embedding_str = str(final_embedding)[1:-1]
	
	# 3. Rewire relationships
	query_fetch_rels = """
	UNWIND $duplicate_uuids AS dup_uuid
	MATCH (duplicate {uuid: dup_uuid})-[r]->(target) RETURN type(r) AS rel_type, properties(r) AS props, dup_uuid AS source_uuid, target.uuid AS target_uuid
	UNION
	UNWIND $duplicate_uuids AS dup_uuid
	MATCH (source)-[r]->(duplicate {uuid: dup_uuid}) RETURN type(r) AS rel_type, properties(r) AS props, source.uuid AS source_uuid, dup_uuid AS target_uuid
	"""
	rel_results = await execute_query(query_fetch_rels, database=db_name, duplicate_uuids=duplicate_uuids)
	
	rewired_count = 0

	if rel_results:
		for record in rel_results:
			rel_type = record["rel_type"]
			props = record["props"]
			source_uuid = record["source_uuid"]
			target_uuid = record["target_uuid"]
			
			new_source_uuid = canonical_uuid if source_uuid in duplicate_uuids else source_uuid
			new_target_uuid = canonical_uuid if target_uuid in duplicate_uuids else target_uuid
			if new_source_uuid == new_target_uuid:
				continue
			
			prop_list = []
			for key, value in props.items():
				if key == 'fact_embedding' and value is not None:
					# The value is already a list from the DB, str(value) gives '[0.1, ...]'
					prop_list.append(f"{key}: vecf32({str(value)})")
				else:
					# Use json.dumps for all other types for safe string formatting
					prop_list.append(f"{key}: {json.dumps(value)}")
			
			props_str = ", ".join(prop_list)

			# Create the new relationship with the correctly formatted properties
			query_rewire_rel = f"""
			MATCH (a:Entity {{uuid: $source}}), (b:Entity {{uuid: $target}})
			CREATE (a)-[r:`{rel_type}` {{{props_str}}}]->(b)
			"""
			
			await execute_query(query_rewire_rel, database=db_name, source=new_source_uuid, target=new_target_uuid)
			rewired_count += 1
	
	print(f"  - Successfully rewired {rewired_count} relationships.")


	# 4. Update canonical node and delete the old duplicates
	query_cleanup = f"""
	MATCH (canonical:Entity {{uuid: $canonical_uuid}})
	SET canonical.summary = $final_summary,
		canonical.name_embedding = vecf32([{embedding_str}])
	WITH canonical
	UNWIND $duplicate_uuids AS dup_uuid
	MATCH (duplicate:Entity {{uuid: dup_uuid}})
	DETACH DELETE duplicate
	"""
	await execute_query(query_cleanup, database=db_name, 
						canonical_uuid=canonical_uuid, 
						duplicate_uuids=duplicate_uuids, 
						final_summary=final_summary)
	
	print(f"  - Node merge complete. Canonical node {canonical_uuid[:8]} updated with new summary and embedding.")


async def advanced_deduplication_controller(db_name: str, node_threshold=0.91):
	"""
	Main controller to orchestrate the advanced deduplication and merge process.
	"""
	print("\n===== Starting Advanced Deduplication and Consolidation Process =====")
	
	# 1. Find and process duplicate NODE communities
	duplicate_node_communities = await find_duplicate_communities(db_name, node_threshold)

	if not duplicate_node_communities:
		print("\n===== Deduplication complete. No node communities found. =====")
		return

	for community in duplicate_node_communities:
		if len(community) < 2:
			continue
			
		print(f"\n--- Processing Node Community: {community} ---")
		try:
			# 2. Select the best node to be the survivor
			canonical_uuid = await select_canonical_node(db_name, community)
			duplicate_uuids = [uuid for uuid in community if uuid != canonical_uuid]
			
			# 3. Merge nodes and rewire relationships
			await merge_and_consolidate_nodes(db_name, canonical_uuid, duplicate_uuids)
			
			# 4. NEW: Run semantic edge consolidation on the canonical node
			await consolidate_edges_for_node(db_name, canonical_uuid)

		except Exception as e:
			print(f"Could not process community {community}. Error: {e}")

	print("\n===== Advanced deduplication and consolidation process complete. =====")