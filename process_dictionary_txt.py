import re
import json
import jsonlines
from dataclasses import dataclass, asdict
from typing import List, Optional

# Mapa de caracteres para normalização
char_map = {
    '@': 'ã',  # Converter @ para ã
    '$': 'th',  # Converter $ para th
    '√': 'ãi',  # Converter √ para ãi
    '@o': 'io'  # Converter @o para io
}

@dataclass
class YanomamiExample:
    original: str
    translation: str

@dataclass
class YanomamiEntry:
    headword: str
    grammar_info: Optional[str]
    definition: str
    examples: List[YanomamiExample]
    related_terms: List[str]

def normalize_text(text: str) -> str:
    """Normalize text by fixing common OCR errors."""
    for wrong, correct in char_map.items():
        text = text.replace(wrong, correct)
    
    # Remove espaços extras
    text = re.sub(r'\s+', ' ', text)
    
    # Juntar caracteres que foram separados
    text = re.sub(r'([a-z])\s+(th|ã)\s+([a-z])', r'\1\2\3', text)
    
    return text.strip()

def is_entry_start(line: str) -> bool:
    """Determine if a line is the start of a dictionary entry."""
    if not line.strip():
        return False
    
    # Linhas que começam com números ou são continuações
    if re.match(r'^\d+\.|\(cont\.\)', line):
        return False
    
    # Linhas que são apenas referências
    if line.strip().startswith('V.'):
        return False
    
    # Deve começar com palavra Yanomami (geralmente em negrito no PDF)
    return bool(re.match(r'^[a-zëãõ@$√]+', line.strip().lower()))

def process_dictionary_entry(lines: List[str]) -> YanomamiEntry:
    """Process a group of lines that form a dictionary entry."""
    text = ' '.join(lines)
    text = normalize_text(text)
    
    # Extrair o headword (primeira palavra)
    headword = text.split(':')[0].strip()
    
    # Extrair informação gramatical (entre parênteses)
    grammar_info = None
    grammar_match = re.search(r'\((.*?)\)', text)
    if grammar_match:
        grammar_info = grammar_match.group(1)
    
    # Extrair exemplos (formato: original: tradução)
    examples = []
    for example_match in re.finditer(r'([^:]+?):\s*([^.]+)\.', text):
        if not example_match.group(1).startswith('V.'):  # Ignorar referências
            examples.append(YanomamiExample(
                original=normalize_text(example_match.group(1)),
                translation=example_match.group(2).strip()
            ))
    
    # Extrair termos relacionados (após "V.")
    related_terms = []
    related_match = re.search(r'V\.\s+(.+?)(?:\.|$)', text)
    if related_match:
        related_terms = [term.strip() for term in related_match.group(1).split(',')]
    
    # Extrair definição (texto entre o headword e os exemplos/termos relacionados)
    definition = text
    if ':' in text:
        definition = text.split(':', 1)[1]
    definition = re.sub(r'V\.\s+.+$', '', definition)  # Remover termos relacionados
    definition = re.sub(r'\([^)]+\)', '', definition)  # Remover info gramatical
    definition = definition.strip()
    
    return YanomamiEntry(
        headword=normalize_text(headword),
        grammar_info=grammar_info,
        definition=definition,
        examples=examples,
        related_terms=related_terms
    )

def process_dictionary_file(input_file: str, output_json: str, output_vectors: str):
    """Process the dictionary text file and create JSON and vector files."""
    current_entry_lines = []
    entries = []
    
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
                
            if is_entry_start(line):
                if current_entry_lines:
                    try:
                        entry = process_dictionary_entry(current_entry_lines)
                        entries.append(entry)
                    except Exception as e:
                        print(f"Error processing entry: {current_entry_lines}")
                        print(f"Error: {e}")
                current_entry_lines = [line]
            else:
                current_entry_lines.append(line)
    
    # Processar última entrada
    if current_entry_lines:
        try:
            entry = process_dictionary_entry(current_entry_lines)
            entries.append(entry)
        except Exception as e:
            print(f"Error processing entry: {current_entry_lines}")
            print(f"Error: {e}")
    
    # Salvar entradas em JSON
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump([asdict(entry) for entry in entries], f, ensure_ascii=False, indent=2)
    
    # Criar textos para vetorização
    with jsonlines.open(output_vectors, 'w') as writer:
        for entry in entries:
            # Texto base com headword e definição
            text = f"{entry.headword}: {entry.definition}"
            
            # Adicionar exemplos se existirem
            if entry.examples:
                examples_text = ". ".join(
                    f"{ex.original}: {ex.translation}" 
                    for ex in entry.examples
                )
                text += f". Exemplos: {examples_text}"
            
            writer.write({"text": text})

if __name__ == "__main__":
    input_file = "Yanomamo-Dictionary-Complete.txt"
    output_json = "dictionary_entries.json"
    output_vectors = "vector_texts.jsonl"
    
    process_dictionary_file(input_file, output_json, output_vectors)
