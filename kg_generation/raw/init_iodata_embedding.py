import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModel
import sqlite3

# Load model and tokenizer
model_name = 'BAAI/bge-m3'
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)

device = 'cuda'
model.to(device)

# Dictionary to store embeddings
entity_embeddings = {}

# Function to generate embeddings
def generate_embedding(text):
    input = tokenizer(text, return_tensors='pt', padding=True, truncation=True).to(device)
    with torch.no_grad():
        output = model(**input)
        embedding = output.last_hidden_state[:, 0, :]
        embedding = torch.nn.functional.normalize(embedding, p=2, dim=1)
        return embedding

# Connect to SQLite database
conn = sqlite3.connect('example.db')

# Create a cursor object to execute SQL statements
cur = conn.cursor()

try:
    # Execute query to read id and data columns from io_data table
    cur.execute("SELECT id, data FROM io_data")
    
    # Fetch the query results
    rows = cur.fetchall()

    # Output the results
    for row in rows:
        cur_id = row[0]
        cur_name = row[1]
        if not cur_name:
            cur_name = 'None'
        embedding = generate_embedding(cur_name)
        entity_embeddings[cur_id] = embedding

    # Save the embeddings to a file
    torch.save(entity_embeddings, 'data_entity.pth')

    print("Embeddings have been saved to data_entity.pth")

except sqlite3.OperationalError as e:
    print(f"Error: {e}")

finally:
    # Close the connection
    conn.close()
