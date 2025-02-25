from sentence_transformers import SentenceTransformer
from annoy import AnnoyIndex
import pickle

def load_data():
    # Carregar o índice Annoy
    with open('dictionary_data.pkl', 'rb') as f:
        data = pickle.load(f)
    
    # Carregar modelo
    model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
    
    # Carregar índice
    dimension = len(model.encode(['dummy'])[0])
    index = AnnoyIndex(dimension, 'angular')
    index.load('dictionary.ann')
    
    return index, data['texts'], data['entries'], model

def search_dictionary(query, k=3):
    """
    Pesquisar no dicionário usando combinação de similaridade semântica e busca por texto.
    
    Args:
        query: String com a consulta
        k: Número de resultados para retornar na busca semântica
    """
    # Carregar dados
    index, texts, entries, model = load_data()
    
    # Criar embedding da query
    query_embedding = model.encode([query])[0]
    
    # Buscar os k vizinhos mais próximos
    nearest_ids, distances = index.get_nns_by_vector(query_embedding, k, include_distances=True)
    
    # Busca por texto (case insensitive)
    query_terms = query.lower().split()
    text_matches = set()
    
    # Procurar em todas as entradas
    for idx, entry in enumerate(entries):
        # Verificar no headword e definição
        text = (entry['headword'] + ' ' + entry['definition']).lower()
        
        # Verificar nos exemplos
        if entry['examples']:
            for ex in entry['examples']:
                text += ' ' + ex['original'].lower() + ' ' + ex['translation'].lower()
        
        # Se todos os termos da busca estão presentes
        if all(term in text for term in query_terms):
            text_matches.add(idx)
    
    # Combinar resultados
    results = []
    seen_ids = set()
    
    # Primeiro adicionar matches exatos de texto
    for idx in text_matches:
        if idx not in seen_ids:
            seen_ids.add(idx)
            results.append({
                'rank': len(results) + 1,
                'distance': 0.0,  # Score perfeito para matches de texto
                'headword': entries[idx]['headword'],
                'definition': entries[idx]['definition'],
                'examples': entries[idx]['examples'],
                'match_type': 'text'
            })
    
    # Depois adicionar resultados da busca semântica
    for idx, distance in zip(nearest_ids, distances):
        if idx not in seen_ids:
            seen_ids.add(idx)
            results.append({
                'rank': len(results) + 1,
                'distance': float(distance),
                'headword': entries[idx]['headword'],
                'definition': entries[idx]['definition'],
                'examples': entries[idx]['examples'],
                'match_type': 'semantic'
            })
    
    return results[:k]  # Retornar apenas os k melhores resultados

if __name__ == "__main__":
    # Exemplo de uso
    query = input("Digite sua consulta: ")
    results = search_dictionary(query)
    
    print("\nResultados encontrados:")
    for result in results:
        print(f"\n{'='*80}")
        print(f"Entrada {result['rank']}:")
        print(f"Palavra: {result['headword']}")
        print(f"Tipo de match: {result['match_type']}")
        if result['match_type'] == 'semantic':
            print(f"Score de similaridade: {(1 - result['distance']):.3f}")
        print(f"\nDefinição:\n{result['definition']}")
        if result['examples']:
            print("\nExemplos:")
            for ex in result['examples']:
                print(f"• Original: {ex['original']}")
                print(f"  Tradução: {ex['translation']}")
        print()
