from kg_extractor import extract_knowledge_graph
from kg_extractor.input_text import text

if __name__ == "__main__":
    db_name = "example_db"
    extract_knowledge_graph(text, db_name)
