from falkordb.asyncio import FalkorDB
from .config import db_client
from datetime import datetime, timedelta, timezone

def convert_datetimes_to_strings(obj):
	if isinstance(obj, dict):
		return {k: convert_datetimes_to_strings(v) for k, v in obj.items()}
	elif isinstance(obj, list):
		return [convert_datetimes_to_strings(item) for item in obj]
	elif isinstance(obj, tuple):
		return tuple(convert_datetimes_to_strings(item) for item in obj)
	elif isinstance(obj, datetime):
		return obj.isoformat()
	else:
		return obj

async def execute_query(cypher_query_, database='default', **kwargs):
		graph = db_client.select_graph(database)
  
		params = convert_datetimes_to_strings(dict(kwargs))
		try:
			result = await graph.query(cypher_query_, params=params)
		except Exception as e:
			print(f'Error executing FalkorDB query: {e}\n{cypher_query_}\n{params}')
			raise
   
		header = [h[1] for h in result.header]
  
		if not result.result_set:
			return None

		records = []
		for row in result.result_set:
			records.append(dict(zip(header, row)))
		return records

## DB OPERATION

async def get_node_from_uuid(uuid, db_name):
	query = """MATCH (n:Entity {uuid: '""" + uuid + """'})
			RETURN
				n.name AS name,
				n.summary AS summary,
				n.uuid AS uuid
			"""
	res = await execute_query(query, db_name)
	try:
		return res[0]
	except:
		return None

async def get_uuid_from_name(name, db_name):
	query = "MATCH (n:Entity {name: $name}) RETURN n.uuid AS uuid"
	params = {"name": name}
	
	record = await execute_query(query,db_name, **params)

	try:
		record = record[0]
	except:
		return None

	if record and 'uuid' in record:
		return record['uuid']
	else:
		return None