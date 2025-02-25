import json
from sentence_transformers import SentenceTransformer
import numpy as np
from annoy import AnnoyIndex
import pickle

def load_dictionary():
    with open('dictionary_entries.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def create_texts_for_embedding(entries):
    """Criar textos formatados para embedding de cada entrada do dicionário."""
    texts = []
    for entry in entries:
        # Combinar headword, definição e exemplos em um texto
        text = f"{entry['headword']}: {entry['definition']}"
        if entry['examples']:
            examples_text = ". ".join(
                f"{ex['original']}: {ex['translation']}" 
                for ex in entry['examples']
            )
            text += f". Exemplos: {examples_text}"
        texts.append(text)
    return texts

def main():
    print("Carregando o dicionário...")
    entries = load_dictionary()
    
    print("Preparando textos para embedding...")
    texts = create_texts_for_embedding(entries)
    
    print("Carregando modelo de embedding...")
    model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
    
    print("Criando embeddings...")
    embeddings = model.encode(texts, show_progress_bar=True)
    
    print("Criando índice Annoy...")
    # Criar índice Annoy
    dimension = len(embeddings[0])
    index = AnnoyIndex(dimension, 'angular')  # angular distance é bom para embeddings normalizados
    
    # Adicionar vetores ao índice
    for i, embedding in enumerate(embeddings):
        index.add_item(i, embedding)
    
    # Construir o índice com 10 árvores (mais árvores = mais precisão, mas mais memória)
    index.build(10)
    
    print("Salvando dados...")
    # Salvar o índice Annoy
    index.save('dictionary.ann')
    
    # Salvar textos e entradas para referência
    with open('dictionary_data.pkl', 'wb') as f:
        pickle.dump({
            'texts': texts,
            'entries': entries
        }, f)
    
    print("Concluído! Os arquivos dictionary.ann e dictionary_data.pkl foram criados.")

if __name__ == "__main__":
    main()
