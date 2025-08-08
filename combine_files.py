import os

output_file = "iterative_combined_output.txt"
workspace_dir = "/Users/thubpham/knowledge_graph_ingestion"  # folder
excluded_dirs = {"__init__.py", "input_text.py", "utils.py", "__pycache__"}

with open(output_file, "w", encoding="utf-8") as outfile:
    for root, dirs, files in os.walk(workspace_dir):
        # Remove excluded directories from traversal
        dirs[:] = [d for d in dirs if d not in excluded_dirs]
        for file in files:
            if file == output_file or file.startswith(".") or file.endswith(".pyc"):
                continue  # Skip the output file itself, hidden files, or bytecode

            file_path = os.path.join(root, file)

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    outfile.write(f"\n--- {file_path} ---\n")
                    outfile.write(f.read())
            except Exception as e:
                print(f"Could not read {file_path}: {e}")
