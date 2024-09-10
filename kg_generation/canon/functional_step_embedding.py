import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModel

model_name = 'BAAI/bge-m3'
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)

device = 'cuda'
model.to(device)

entity_embeddings = {}
def generate_embedding(text):
    input = tokenizer(text, return_tensors='pt', padding=True, truncation=True).to(device)
    with torch.no_grad():
        output = model(**input)
        embedding = output.last_hidden_state[:,0,:]
        embedding = torch.nn.functional.normalize(embedding, p=2, dim=1)
        return embedding



df = pd.read_csv(r'functional_step_entities_with_content.csv')
count = df.shape[0]
for _, row in df.iterrows():
    cur_id = row['id']
    short_name = row['content']
    embedding = generate_embedding(short_name)
    entity_embeddings[cur_id] = embedding
    count = count - 1
    print(f"Embedding for {cur_id}: {short_name} have been saved to step_entity_preprocessing.pth, {count} left")
torch.save(entity_embeddings, 'step_entity_preprocessing.pth')
