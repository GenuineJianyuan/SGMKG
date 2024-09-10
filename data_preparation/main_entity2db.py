import os
import sqlite3

# Folder paths
input_folder = r'YOUR_FUNCTIONAL_STEP_FOLDER_PATH'
workflow_folder = r'YOUR_WORKFLOW_SAVING_FOLDER_PATH'

# Connect to the SQLite database (create if it doesn't exist)
conn = sqlite3.connect('example.db')

# Create a cursor object to execute SQL statements
cur = conn.cursor()

# Create the 'script' table
cur.execute('''CREATE TABLE IF NOT EXISTS script (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               script_name TEXT,
               code_summarization TEXT)''')

# Create the 'step' table
cur.execute('''CREATE TABLE IF NOT EXISTS step (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               step_name TEXT,
               short_name TEXT,
               description TEXT,
               input TEXT,
               output TEXT,
               script_id INTEGER)''')

# Create the 'io_data' table
cur.execute('''CREATE TABLE IF NOT EXISTS io_data (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               step_id INTEGER,
               data TEXT,
               data_type TEXT)''')

# Create the 'step_workflow' table
cur.execute('''CREATE TABLE IF NOT EXISTS step_workflow (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               script_id INTEGER,
               output_step_id INTEGER,
               input_step_id INTEGER)''')

# Log filenames that encountered errors
error_files = []

# Retrieve filenames from the folder
sample_files = os.listdir(input_folder)

# Process these files
for file_name in sample_files:
    if file_name.endswith('.txt'):
        try:
            # Start transaction
            conn.execute('BEGIN TRANSACTION')
            
            file_path = os.path.join(input_folder, file_name)
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                cur_summ = f.read()
            cur_dir = eval(cur_summ.split("json")[1].split("")[0])
            cur_summarization = cur_dir["Code summarization"]
            script_name = file_name
            
            # Insert data into the 'script' table
            cur.execute("INSERT INTO script (script_name, code_summarization) VALUES (?, ?)", (script_name, cur_summarization))
            script_id = cur.lastrowid  # Get the ID of the newly inserted script
            print(f"{file_name}:{script_id} added to database.")
            
            # Process each step and insert data into the 'step' table
            for step_obj in cur_dir["Step"]:
                step_name = step_obj["Step name"].strip()
                short_name = step_obj["Short Name"]
                description = step_obj["Step description"]
                input_str = ' | '.join(step_obj["Input"])
                output_str = ' | '.join(step_obj["Output"])
                cur.execute("INSERT INTO step (step_name, short_name, description, input, output, script_id) VALUES (?, ?, ?, ?, ?, ?)",
                            (step_name, short_name, description, input_str, output_str, script_id))
                step_id = cur.lastrowid  # Get the ID of the newly inserted step
                
                # Insert input data items of each step into the 'io_data' table
                for input_data in step_obj["Input"]:
                    cur.execute("INSERT INTO io_data (step_id, data, data_type) VALUES (?, ?, ?)", (step_id, input_data, "input"))
                
                # Insert output data items of each step into the 'io_data' table
                for output_data in step_obj["Output"]:
                    cur.execute("INSERT INTO io_data (step_id, data, data_type) VALUES (?, ?, ?)", (step_id, output_data, "output"))
                
                print(f"Step '{step_name}' added to database.")
            
            # Process each workflow and insert data into the 'step_workflow' table
            workflow_file_path = os.path.join(workflow_folder, script_name)
            with open(workflow_file_path, 'r', encoding='utf-8-sig') as f:
                cur_workflow = f.read()
            workflow_data = eval(cur_workflow)[script_name]
            
            # Traverse workflow data, parse relationships, and insert into the 'step_workflow' table
            for relation in workflow_data:
                source, target = relation.split(';')
                output_step_name = source.replace(" ","")
                input_step_name = target.replace(" ","")
                
                # Query the output step ID
                cur.execute("SELECT id FROM step WHERE step_name = ? AND script_id = ?", (output_step_name, script_id))
                output_step_id = cur.fetchone()[0]
                
                # Query the input step ID
                cur.execute("SELECT id FROM step WHERE step_name = ? AND script_id = ?", (input_step_name, script_id))
                input_step_id = cur.fetchone()[0]
                
                if not output_step_id or not input_step_id:
                    raise ValueError(f"Error: Could not find step IDs for {output_step_name}, {input_step_name}")
                
                # Insert the relationship into the 'step_workflow' table
                cur.execute("INSERT INTO step_workflow (script_id, output_step_id, input_step_id) VALUES (?, ?, ?)",
                            (script_id, output_step_id, input_step_id))
                print(f"Relationship between '{output_step_name}' and '{input_step_name}' added to step_workflow.")
            
            # Commit transaction
            conn.commit()

        except Exception as e:
            # Rollback transaction if an error occurs
            conn.rollback()
            error_files.append(file_name)
            print(f"Error processing {file_name}: {e}")

# Output the filenames that encountered errors
if error_files:
    print("The following files encountered errors and were not processed:")
    for error_file in error_files:
        print(error_file)

# Close connection
conn.close()
