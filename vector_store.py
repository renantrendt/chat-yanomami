from annoy import AnnoyIndex
from transformers import AutoTokenizer, AutoModel
import torch
import numpy as np
import json

class VectorStore:
    def __init__(self, model_name="sentence-transformers/all-MiniLM-L6-v2"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.vector_dim = 384  # dimension for all-MiniLM-L6-v2
        self.index = AnnoyIndex(self.vector_dim, 'angular')
        self.content_map = {}
        
    def _get_embedding(self, text):
        inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
        with torch.no_grad():
            outputs = self.model(**inputs)
        # Use mean pooling to get text embedding
        embeddings = outputs.last_hidden_state.mean(dim=1)
        return embeddings[0].numpy()
    
    def add_content(self, texts, save_path="vectors.ann"):
        """Add content to the vector store"""
        for i, text in enumerate(texts):
            vector = self._get_embedding(text)
            self.index.add_item(i, vector)
            self.content_map[i] = text
            
        self.index.build(10)  # 10 trees for better accuracy
        self.index.save(save_path)
        
        # Save the content map
        with open(save_path + ".json", "w") as f:
            json.dump(self.content_map, f)
    
    def load(self, path="vectors.ann"):
        """Load existing vector store"""
        self.index.load(path)
        with open(path + ".json", "r") as f:
            self.content_map = json.load(f)
    
    def search(self, query, k=3):
        """Search k most similar texts"""
        query_vector = self._get_embedding(query)
        similar_ids, distances = self.index.get_nns_by_vector(query_vector, k, include_distances=True)
        results = []
        for idx, dist in zip(similar_ids, distances):
            results.append({
                "content": self.content_map[str(idx)],
                "similarity": 1 - dist  # convert distance to similarity score
            })
        return results

if __name__ == "__main__":
    # Example usage
    store = VectorStore()
    # Add your content here
    texts = [
        "Example text 1",
        "Example text 2",
    ]
    store.add_content(texts)
