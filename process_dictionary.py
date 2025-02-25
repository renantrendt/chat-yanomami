import re
import json
import pdfplumber
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

@dataclass
class YanomamiExample:
    yanomami: str
    spanish: str
    context: Optional[str] = None

@dataclass
class YanomamiEntry:
    headword: str
    grammatical_info: List[str]
    definition: str
    examples: List[YanomamiExample]
    related_terms: List[str]
    semantic_field: Optional[str]
    dialectal_variants: Dict[str, str]
    cultural_notes: Optional[str]
    etymology: Optional[str]
    full_content: str

    def to_dict(self) -> Dict:
        return {
            'headword': self.headword,
            'grammatical_info': self.grammatical_info,
            'definition': self.definition,
            'examples': [{'yanomami': ex.yanomami, 'spanish': ex.spanish, 'context': ex.context} for ex in self.examples],
            'related_terms': self.related_terms,
            'semantic_field': self.semantic_field,
            'dialectal_variants': self.dialectal_variants,
            'cultural_notes': self.cultural_notes,
            'etymology': self.etymology,
            'full_content': self.full_content
        }

def clean_text(text: str) -> str:
    """Clean and normalize text while preserving linguistic information."""
    if not text:
        return ''
    
    # Create a mapping of special characters to their normalized form
    char_map = {
        # Vogais nasais e suas variantes
        'ã': 'ã',  # Nasal a
        'õ': 'õ',  # Nasal o
        'ĩ': 'ĩ',  # Nasal i
        'ũ': 'ũ',  # Nasal u
        'ẽ': 'ẽ',  # Nasal e
        'ā': 'ã',  # Variante de a nasal
        'ō': 'õ',  # Variante de o nasal
        'ī': 'ĩ',  # Variante de i nasal
        'ū': 'ũ',  # Variante de u nasal
        'ē': 'ẽ',  # Variante de e nasal
        
        # Vogais com trema e variantes
        'ë': 'ë',  # Central e
        'ï': 'ï',  # Central i
        'ü': 'ü',  # Central u
        'ö': 'ö',  # Central o
        'ä': 'ä',  # Central a
        'e\u0308': 'ë',  # e + combining diaeresis
        'i\u0308': 'ï',  # i + combining diaeresis
        'u\u0308': 'ü',  # u + combining diaeresis
        'o\u0308': 'ö',  # o + combining diaeresis
        'a\u0308': 'ä',  # a + combining diaeresis
        
        # Caracteres especiais do PDF e suas variantes
        '@': '@',    # Vogal central especial
        '∏': 'ĩ',    # Forma alternativa de i nasal
        '∞': 'õ',    # Forma alternativa de o nasal
        't$': 't̃',   # t com til
        'n$': 'ñ',   # n com til
        't\u0303': 't̃',  # t + combining tilde
        'n\u0303': 'ñ',  # n + combining tilde
        
        # Marcadores morfológicos e estruturais
        '√': '',     # Marcador de raiz
        '✓': '',     # Marcador alternativo
        '•': '',     # Marcador de item
        '◊': '',     # Marcador de variante
        '○': '',     # Marcador circular
        '¶': '',     # Marcador de parágrafo
        '§': '',     # Marcador de seção
        
        # Símbolos de tradução e referência
        '→': '=',    # Seta indicando tradução
        '⇒': '=',    # Seta dupla
        '≈': '~',    # Aproximadamente
        '†': '*',    # Cruz (nota)
        '‡': '**',   # Cruz dupla (nota importante)
        '=': '=',    # Igual (manter)
        ':': ':',    # Dois pontos (manter)
        
        # Outros caracteres especiais
        '\u200b': '',  # Zero-width space
        '\u200c': '',  # Zero-width non-joiner
        '\u200d': '',  # Zero-width joiner
        '\ufeff': '',  # Zero-width no-break space (BOM)
        '\xa0': ' ',   # Non-breaking space
    }
    
    # Normalize Unicode decomposed forms
    text = text.replace('t$', char_map['t$'])
    text = text.replace('n$', char_map['n$'])
    
    # Handle multi-character sequences first
    for seq in ['t\u0303', 'n\u0303', 'e\u0308', 'i\u0308', 'u\u0308', 'o\u0308', 'a\u0308']:
        if seq in text:
            text = text.replace(seq, char_map[seq])
    
    # Then handle single character replacements
    for special_char, replacement in char_map.items():
        if len(special_char) == 1:  # Only replace single characters
            text = text.replace(special_char, replacement)
    
    # Remove multiple spaces and normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    return text

def extract_dialectal_variants(content: str) -> Dict[str, str]:
    """Extract dialectal variants marked with (hra) and (hsh)."""
    variants = {}
    
    # Look for variants marked with (hra) - ora teri dialect
    ora_teri = re.findall(r'\(hra\)\s*([^;.()]+)', content)
    if ora_teri:
        variants['ora_teri'] = [v.strip() for v in ora_teri]
    
    # Look for variants marked with (hsh) - shamatari dialect
    shamatari = re.findall(r'\(hsh\)\s*([^;.()]+)', content)
    if shamatari:
        variants['shamatari'] = [v.strip() for v in shamatari]
    
    return variants

def extract_cultural_notes(content: str) -> Optional[str]:
    """Extract cultural information and notes about usage."""
    # Look for content between parentheses that describes cultural context
    cultural_matches = re.findall(r'\((?!hra|hsh)[^)]*costumbre[^)]*\)', content, re.IGNORECASE)
    cultural_matches.extend(re.findall(r'\((?!hra|hsh)[^)]*creencia[^)]*\)', content, re.IGNORECASE))
    
    if cultural_matches:
        return ' '.join(cultural_matches)
    return None

def process_dictionary_entry(lines: List[str]) -> Optional[YanomamiEntry]:
    """Process a group of lines that form a dictionary entry."""
    if not lines:
        return None
    
    # Clean and join lines for processing
    content = ' '.join(lines)
    content = re.sub(r'\s+', ' ', content)  # Normalize whitespace
    content = re.sub(r'\d+\s*$', '', content)  # Remove page numbers at end
    content = re.sub(r'^\d+\s+', '', content)  # Remove page numbers at start
    content = re.sub(r'\b\d+\s*Diccionario\b.*?\byãnomãm@\b', '', content)  # Remove headers
    
    # Extract headword - should be at the start of the entry
    headword_match = re.match(r'^([^\s.,;:]+)', content)
    if not headword_match:
        return None
    
    headword = clean_text(headword_match.group(1))
    if not headword or len(headword) < 2:
        return None
    
    # Skip if headword looks like a page header or footer
    if re.match(r'^Diccionario|^[A-Z][a-z]+\s*\d{4}$', headword):
        return None
    
    # Extract definition - everything up to the first numbered section or grammatical marker
    definition = ''
    def_match = re.search(r'^[^\d]+?(?=\d\.\s|\b(?:vb\.|adj\.|sust\.|pron\.)\b|$)', content)
    if def_match:
        definition = clean_text(def_match.group(0))
    
    # Extract grammatical information
    gram_info = []
    gram_patterns = [
        (r'\b(vb\.|adj\.|sust\.|pron\.|clasif\.|v\.|adv\.|prep\.|conj\.|interj\.|num\.|part\.)\s*(\w+\.?)?\b', 'abbr'),
        (r'\b(verbo|adjetivo|sustantivo|pronombre|clasificador|adverbio|preposición|conjunción|interjección|numeral|partícula)\b', 'full')
    ]
    
    for pattern, type_ in gram_patterns:
        for match in re.finditer(pattern, content, re.IGNORECASE):
            info = match.group(1).lower()
            if type_ == 'full':
                info = {
                    'verbo': 'vb.',
                    'adjetivo': 'adj.',
                    'sustantivo': 'sust.',
                    'pronombre': 'pron.',
                    'clasificador': 'clasif.',
                    'adverbio': 'adv.',
                    'preposición': 'prep.',
                    'conjunción': 'conj.',
                    'interjección': 'interj.',
                    'numeral': 'num.',
                    'partícula': 'part.'
                }.get(info, info)
            
            # Add any modifiers
            if match.group(2):
                info += ' ' + match.group(2)
            
            if info and info not in gram_info:
                gram_info.append(info)
    
    # Extract examples
    examples = []
    example_patterns = [
        # Padrão 1: Exemplo em yanomami seguido de dois pontos e tradução
        r'([^:;.]+?):\s*([^;.]+?)(?=[.;]|$)',
        
        # Padrão 2: Exemplo entre aspas com tradução
        r'"([^"]+)"\s*(?:=|→)\s*"([^"]+)"',
        
        # Padrão 3: Exemplo com seta ou igual
        r'([^.!?:]+?)\s*(?:=|→)\s*([^.!?;]+)',
        
        # Padrão 4: Exemplo com kë ou ha
        r'([^.;]+?\b(?:kë|ha)\b[^:;.]+?):\s*([^;.]+)'
    ]
    
    for pattern in example_patterns:
        for match in re.finditer(pattern, content):
            yanomami = clean_text(match.group(1))
            spanish = clean_text(match.group(2))
            
            # Verificar se é realmente um exemplo válido
            if yanomami and spanish and \
               len(yanomami.split()) > 1 and \
               not any(yanomami.startswith(w) for w in ['V.', 'cf.', 'sin.']):
                
                # Procurar contexto antes do exemplo
                context = None
                context_match = re.search(f'([^.;]+){re.escape(yanomami)}', content)
                if context_match:
                    context = clean_text(context_match.group(1))
                
                examples.append(YanomamiExample(
                    yanomami=yanomami,
                    spanish=spanish,
                    context=context
                ))
    
    # Extract related terms
    related = []
    related_sections = re.findall(r'(?:V\.|cf\.|sin\.|v[eé]ase)\s*([^.;]+)', content)
    for section in related_sections:
        terms = [clean_text(term) for term in re.split(r'[,;]', section)]
        related.extend(term for term in terms if term and term != headword)
    
    # Determine semantic field
    semantic_field = None
    field_patterns = {
        'Bot.': 'Botánica',
        'Zool.': 'Zoología',
        'Orn.': 'Ornitología',
        'Anat.': 'Anatomía',
        'Med.': 'Medicina',
        'Mit.': 'Mitología',
        'Cham.': 'Chamanismo'
    }
    for abbr, full in field_patterns.items():
        if re.search(fr'\b{abbr}\b', content):
            semantic_field = full
            break
    
    # Extract dialectal variants
    dialectal_variants = extract_dialectal_variants(content)
    
    # Extract cultural notes
    cultural_notes = extract_cultural_notes(content)
    
    # Extract etymology
    etymology = None
    etym_patterns = [
        r'\(Del[^)]+\)',
        r'\bDe\b[^.]+\.',
        r'\bEtimología:\s*[^.]+\.'
    ]
    for pattern in etym_patterns:
        match = re.search(pattern, content)
        if match:
            etymology = clean_text(match.group(0))
            break
    
    # Criar a entrada apenas se tiver conteúdo significativo
    if headword and (definition or examples or gram_info or cultural_notes or dialectal_variants):
        return YanomamiEntry(
            headword=headword,
            grammatical_info=gram_info,
            definition=definition,
            examples=examples,
            related_terms=related,
            semantic_field=semantic_field,
            dialectal_variants=dialectal_variants,
            cultural_notes=cultural_notes,
            etymology=etymology,
            full_content=clean_text(content)
        )
    
    return None
    
    return YanomamiEntry(
        headword=clean_text(headword),
        grammatical_info=gram_info,
        definition=definition,
        examples=examples,
        related_terms=related,
        semantic_field=semantic_field,
        dialectal_variants=dialectal_variants,
        cultural_notes=cultural_notes,
        etymology=etymology,
        full_content=clean_text(content)
    )

def extract_page_content(page) -> str:
    """Extract text content from a PDF page while preserving special characters."""
    # Extract text with custom settings to better handle special characters
    text = page.extract_text(
        x_tolerance=3,  # Adjust horizontal text grouping
        y_tolerance=3,  # Adjust vertical text grouping
        layout=True,    # Use layout analysis
        keep_blank_chars=True  # Keep spaces and special characters
    )
    
    # Remove multiple spaces and normalize line endings
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n\s*\n', '\n', text)
    
    return text

def is_entry_start(line: str) -> bool:
    """Check if a line is the start of a new dictionary entry."""
    if not line or len(line.strip()) == 0:
        return False
    
    line = line.strip()
    
    # Remove page numbers and other noise
    line = re.sub(r'^\d+\s+', '', line)
    line = re.sub(r'\s+\d+$', '', line)
    
    # Skip headers, footers, and special sections
    if any([
        re.match(r'^Diccionario|^[A-Z][a-z]+ \d{4}$', line),  # Headers/footers
        re.match(r'^[\W_]+$', line),  # Lines with only symbols
        line.isupper() and len(line) > 3,  # All caps headers
        len(line) > 100,  # Extremely long lines
        len(line) < 2,  # Very short lines
        re.match(r'^\d+\.\d+$', line),  # Section numbers
        re.match(r'^\s*\d+\s*$', line),  # Just numbers
        re.match(r'^\s*[a-z]+\s*[.)]\s*$', line),  # Just letters with period or parenthesis
        re.match(r'^\s*[()\[\]{}]\s*$', line)  # Just brackets
    ]):
        return False
    
    # Remove common prefixes that might appear at start of lines
    line = re.sub(r'^[0-9]+\.?\s*', '', line)  # Remove numbered lists
    line = re.sub(r'^[a-z]\.\s*', '', line)  # Remove letter lists
    line = re.sub(r'^[-•●*]\s*', '', line)  # Remove bullet points
    
    # Check for non-entry prefixes
    non_entry_prefixes = [
        # Grammatical markers
        'Bot.', 'Zool.', 'Anat.', 'Med.', 'Orn.',
        'V.', 'sin.', 'ant.', 'cf.', 'p.', 'pp.',
        'Véase', 'Ver', 'Comp.', 'Var.',
        'vb.', 'adj.', 'sust.', 'pron.', 'adv.',
        'prep.', 'conj.', 'interj.',
        
        # Structural markers
        'Nota:', 'Ref.:', 'Fig.:', 'N.B.:',
        'Diccionario', 'Ejemplo', 'Ej.',
        
        # Common Spanish words
        'El', 'La', 'Los', 'Las', 'Un', 'Una',
        'Este', 'Esta', 'Estos', 'Estas',
        'Cuando', 'Como', 'Donde', 'Porque',
        
        # Numbers and bullets
        '1.', '2.', '3.', '4.', '5.',
        'a)', 'b)', 'c)', 'd)', 'e)'
    ]
    
    if any(line.startswith(prefix) for prefix in non_entry_prefixes):
        return False
    
    # Check for Yanomami characters
    yanomami_chars = {
        # Vogais nasais e variantes
        'ã', 'õ', 'ĩ', 'ũ', 'ẽ',  # ã, õ, ĩ, ũ, ẽ
        'ā', 'ō', 'ī', 'ū', 'ē',  # ā, ō, ī, ū, ē
        
        # Vogais com trema
        'ë', 'ï', 'ü', 'ö', 'ä',  # ë, ï, ü, ö, ä
        
        # Caracteres especiais
        '@', '∏', '∞',  # @, ∏, ∞
        't̃', 'ñ',  # t̃, ñ
        
        # Outros diacríticos
        '̀', '́', '̂', '̃', '̈'  # Combining diacritics
    }
    
    # Get first word and check if it's a valid entry start
    first_word = line.split()[0] if line.split() else ''
    
    # Entry must start with a letter and contain Yanomami characters
    # or be a simple word (2-20 chars) without special characters
    is_yanomami_word = (
        first_word and
        first_word[0].isalpha() and
        2 <= len(first_word) <= 20 and
        (
            any(c in first_word for c in yanomami_chars) or
            all(c.isalpha() for c in first_word)
        )
    )
    
    # Check for typical dictionary entry patterns
    has_entry_pattern = bool(re.match(
        r'^[a-zA-Zãõĩë@]'  # Starts with letter or special char
        r'[a-zA-Zãõĩë@\s]*'  # More letters/spaces
        r'(?:\s*\([^)]+\))?'  # Optional parenthetical
        r'\s*(?:[=:]|\b(?:vb\.|adj\.|sust\.)\b)',  # Ends with = or : or gram. marker
        line
    ))
    
    # Additional validation
    if is_yanomami_word:
        # Check for continuations
        if ';' in line[:20] or line.startswith(('y ', 'o ', 'e ')):
            return False
        # Check for incomplete phrases
        if len(line.split()) > 3 and not has_entry_pattern:
            return False
    
    return is_yanomami_word

def process_dictionary_file(file_path: str) -> List[Dict]:
    """Process the PDF dictionary file and return a list of structured entries."""
    entries = []
    current_entry = []
    skip_pages = set()  # Pages to skip (TOC, index, etc.)
    
    try:
        with pdfplumber.open(file_path) as pdf:
            print(f"Processing PDF with {len(pdf.pages)} pages...")
            
            # First pass: identify pages to skip
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                if any(header in text.lower() for header in [
                    'índice', 'contenido', 'tabla', 'apéndice', 'appendix',
                    'bibliografía', 'referencias', 'abreviaturas'
                ]):
                    skip_pages.add(page_num)
            
            # Second pass: process dictionary entries
            for page_num, page in enumerate(pdf.pages):
                if page_num in skip_pages:
                    continue
                
                print(f"Processing page {page_num + 1}/{len(pdf.pages)}")
                
                # Extract text with custom settings
                text = extract_page_content(page)
                
                # Split into lines and clean each line
                lines = []
                for line in text.split('\n'):
                    line = line.strip()
                    
                    # Skip unwanted lines
                    if any([
                        not line,  # Empty lines
                        re.match(r'^\d+\s*$', line),  # Page numbers
                        re.match(r'^Diccionario\s+.*$', line, re.IGNORECASE),  # Headers
                        re.match(r'^[A-Z][a-z]+\s+\d{4}$', line),  # Footer with year
                        line.isupper() and len(line) > 3,  # All caps headers
                        re.match(r'^[\W_]+$', line),  # Lines with only symbols
                        line.count(' ') > 50,  # Extremely long lines (likely merged)
                        len(line) < 2  # Very short lines
                    ]):
                        continue
                    
                    # Clean the line
                    line = re.sub(r'^\d+\s+|\s+\d+$', '', line)  # Remove numbers at start/end
                    line = clean_text(line)
                    
                    if line.strip():
                        lines.append(line)
                
                # Process lines into entries
                for line in lines:
                    if is_entry_start(line):
                        # Process previous entry if it exists
                        if current_entry:
                            processed_entry = process_dictionary_entry(current_entry)
                            if processed_entry and processed_entry.headword:
                                # Verify entry has meaningful content
                                if any([
                                    processed_entry.definition,
                                    processed_entry.examples,
                                    processed_entry.grammatical_info,
                                    processed_entry.cultural_notes,
                                    processed_entry.dialectal_variants
                                ]):
                                    entries.append(processed_entry.to_dict())
                        
                        # Start new entry
                        current_entry = [line]
                    elif current_entry:
                        # Add line to current entry if it's not a duplicate
                        if line != current_entry[-1]:
                            current_entry.append(line)
            
            # Process the last entry
            if current_entry:
                processed_entry = process_dictionary_entry(current_entry)
                if processed_entry and processed_entry.headword:
                    if any([
                        processed_entry.definition,
                        processed_entry.examples,
                        processed_entry.grammatical_info,
                        processed_entry.cultural_notes,
                        processed_entry.dialectal_variants
                    ]):
                        entries.append(processed_entry.to_dict())
    
    except FileNotFoundError:
        print(f"Error: Could not find PDF file '{file_path}'")
        raise
    except Exception as e:
        print(f"Error processing PDF: {str(e)}")
        raise
    
    # Remove duplicate entries
    unique_entries = {}
    for entry in entries:
        headword = entry['headword']
        if headword not in unique_entries or \
           len(entry['full_content']) > len(unique_entries[headword]['full_content']):
            unique_entries[headword] = entry
    
    return list(unique_entries.values())

def create_vector_texts(entries: List[Dict]) -> List[str]:
    """Create formatted texts for vector storage."""
    vector_texts = []
    
    for entry in entries:
        # Create a comprehensive text representation
        text_parts = []
        
        # Add Yanomami word
        text_parts.append(f"Palabra Yanomami: {entry['yanomami']}")
        
        # Add grammatical information
        if 'grammatical_info' in entry:
            text_parts.append(f"Información gramatical: {', '.join(entry['grammatical_info'])}")
        
        # Add semantic field
        if 'semantic_field' in entry:
            text_parts.append(f"Campo semántico: {entry['semantic_field']}")
        
        # Add definition
        if 'definition' in entry:
            text_parts.append(f"Definición: {entry['definition']}")
        
        # Add examples
        if 'examples' in entry:
            text_parts.append("Ejemplos:")
            for example in entry['examples']:
                text_parts.append(f"- Yanomami: {example['yanomami']}")
                text_parts.append(f"  Español: {example['spanish']}")
        
        # Add related terms
        if 'related_terms' in entry:
            text_parts.append(f"Términos relacionados: {', '.join(entry['related_terms'])}")
        
        # Combine all parts into a single text entry
        vector_texts.append('\n'.join(text_parts))
    
    return vector_texts

def main():
    # Process the dictionary
    print("Processing dictionary...")
    entries = process_dictionary_file('Yanomamo-Dictionary-Complete.txt')
    
    # Save structured data
    with open('structured_dictionary.json', 'w', encoding='utf-8') as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(entries)} structured entries to structured_dictionary.json")
    
    # Create vector texts
    vector_texts = create_vector_texts(entries)
    
    # Save vector texts
    with open('vector_texts.json', 'w', encoding='utf-8') as f:
        json.dump(vector_texts, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(vector_texts)} vector texts to vector_texts.json")
    
    # Initialize and save to vector store
    from vector_store import VectorStore
    print("Creating vector store...")
    store = VectorStore()
    store.add_content(vector_texts)
    print("Vector store created and saved!")

def create_vector_texts(entries: List[Dict]) -> List[Dict]:
    """Create formatted texts for vector storage with enhanced context."""
    vector_entries = []
    
    for entry in entries:
        # Create main entry vector
        main_vector = {
            'text': '',
            'metadata': {
                'type': 'entry',
                'headword': entry['headword'],
                'pos': entry.get('grammatical_info', [])
            }
        }
        
        # Build main entry text
        text_parts = [
            f"Yanomami word: {entry['headword']}",
            f"Part of speech: {', '.join(entry.get('grammatical_info', []))}",
            f"Definition: {entry.get('definition', '')}"
        ]
        
        # Add semantic field if available
        if entry.get('semantic_field'):
            text_parts.append(f"Field: {entry['semantic_field']}")
        
        # Add dialectal variations
        if entry.get('dialectal_variants'):
            for dialect, variants in entry['dialectal_variants'].items():
                if variants:
                    text_parts.append(f"{dialect.replace('_', ' ').title()} dialect: {', '.join(variants)}")
        
        # Add cultural notes if available
        if entry.get('cultural_notes'):
            text_parts.append(f"Cultural context: {entry['cultural_notes']}")
        
        # Add etymology if available
        if entry.get('etymology'):
            text_parts.append(f"Etymology: {entry['etymology']}")
        
        # Add related terms
        if entry.get('related_terms'):
            text_parts.append(f"Related terms: {', '.join(entry['related_terms'])}")
        
        main_vector['text'] = ' | '.join(text_parts)
        vector_entries.append(main_vector)
        
        # Create separate vectors for examples
        if entry.get('examples'):
            for example in entry['examples']:
                example_vector = {
                    'text': '',
                    'metadata': {
                        'type': 'example',
                        'headword': entry['headword'],
                        'context': example.get('context')
                    }
                }
                
                example_parts = [
                    f"Yanomami example: {example['yanomami']}",
                    f"Spanish translation: {example['spanish']}"
                ]
                
                if example.get('context'):
                    example_parts.append(f"Context: {example['context']}")
                
                example_vector['text'] = ' | '.join(example_parts)
                vector_entries.append(example_vector)
    
    # Save vector texts in JSONL format for easy processing
    with open('vector_texts.jsonl', 'w', encoding='utf-8') as f:
        for entry in vector_entries:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    return vector_entries

def main():
    """Main function to process dictionary and create vector texts."""
    input_file = 'prototype-dic.pdf'
    
    print(f"Processing Yanomami dictionary from {input_file}...")
    
    try:
        # Process dictionary file
        entries = process_dictionary_file(input_file)
        
        # Save processed entries in JSON format
        output_json = 'yanomami_dictionary.json'
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)
        
        print(f"Processed {len(entries)} dictionary entries")
        print(f"Saved structured dictionary to {output_json}")
        
        # Create and save vector texts
        vector_entries = create_vector_texts(entries)
        print(f"Created {len(vector_entries)} vector entries for embedding")
        print("Saved vector texts to vector_texts.jsonl")
        
        # Print some statistics
        example_count = sum(1 for entry in entries if entry.get('examples'))
        cultural_notes_count = sum(1 for entry in entries if entry.get('cultural_notes'))
        dialect_count = sum(1 for entry in entries if entry.get('dialectal_variants'))
        
        print("\nDictionary Statistics:")
        print(f"Total entries: {len(entries)}")
        print(f"Entries with examples: {example_count}")
        print(f"Entries with cultural notes: {cultural_notes_count}")
        print(f"Entries with dialectal variants: {dialect_count}")
        
    except FileNotFoundError:
        print(f"Error: Could not find dictionary file '{input_file}'")
    except Exception as e:
        print(f"Error processing dictionary: {str(e)}")

if __name__ == "__main__":
    main()
