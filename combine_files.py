import os

output_file = "iterative_combined_output.txt"
workspace_dir = "/Users/thubpham/knowledge_graph_ingestion/knowledge_graph_extractor/kg_extractor"
excluded_dirs = {"__init__.py", "input_text.py", "utils.py", "__pycache__"}

print(f"Starting file traversal...")
print(f"Output file: {output_file}")
print(f"Workspace directory: {workspace_dir}")
print(f"Excluded items: {excluded_dirs}")

# Check if the workspace directory exists
if not os.path.exists(workspace_dir):
    print(f"ERROR: Workspace directory does not exist: {workspace_dir}")
    exit(1)

if not os.path.isdir(workspace_dir):
    print(f"ERROR: Workspace path is not a directory: {workspace_dir}")
    exit(1)

print(f"Directory exists and is accessible.")

# List contents of the directory for debugging
print(f"\nContents of {workspace_dir}:")
try:
    for item in os.listdir(workspace_dir):
        item_path = os.path.join(workspace_dir, item)
        item_type = "DIR" if os.path.isdir(item_path) else "FILE"
        print(f"  {item_type}: {item}")
except Exception as e:
    print(f"ERROR: Cannot list directory contents: {e}")
    exit(1)

files_processed = 0
files_skipped = 0
total_chars_written = 0

with open(output_file, "w", encoding="utf-8") as outfile:
    print(f"\nStarting file traversal...")
    
    for root, dirs, files in os.walk(workspace_dir):
        print(f"\nProcessing directory: {root}")
        print(f"  Subdirectories found: {dirs}")
        print(f"  Files found: {files}")
        
        # Remove excluded directories from traversal
        original_dirs = dirs[:]
        dirs[:] = [d for d in dirs if d not in excluded_dirs]
        removed_dirs = set(original_dirs) - set(dirs)
        if removed_dirs:
            print(f"  Excluded directories: {removed_dirs}")
        
        for file in files:
            file_path = os.path.join(root, file)
            print(f"    Checking file: {file}")
            
            # Check skip conditions
            if file == output_file:
                print(f"      SKIPPED: Output file itself")
                files_skipped += 1
                continue
            
            if file.startswith("."):
                print(f"      SKIPPED: Hidden file")
                files_skipped += 1
                continue
            
            if file.endswith(".pyc"):
                print(f"      SKIPPED: Bytecode file")
                files_skipped += 1
                continue
            
            # Check if file is in excluded list (this might be your issue!)
            if file in excluded_dirs:
                print(f"      SKIPPED: File in excluded list")
                files_skipped += 1
                continue

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    print(f"      PROCESSING: {file}")
                    header = f"\n--- {file_path} ---\n"
                    content = f.read()
                    
                    outfile.write(header)
                    outfile.write(content)
                    
                    chars_written = len(header) + len(content)
                    total_chars_written += chars_written
                    files_processed += 1
                    
                    print(f"        Written {chars_written} characters")
                    
            except Exception as e:
                print(f"      ERROR: Could not read {file_path}: {e}")
                files_skipped += 1

print(f"\n=== SUMMARY ===")
print(f"Files processed: {files_processed}")
print(f"Files skipped: {files_skipped}")
print(f"Total characters written: {total_chars_written}")
print(f"Output file created: {output_file}")

# Verify the output file was created and has content
if os.path.exists(output_file):
    file_size = os.path.getsize(output_file)
    print(f"Output file size: {file_size} bytes")
    if file_size == 0:
        print("WARNING: Output file is empty!")
else:
    print("ERROR: Output file was not created!")