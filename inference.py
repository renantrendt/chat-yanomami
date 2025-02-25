import sys
import logging
import argparse
from transformers import GPT2Tokenizer, TFGPT2LMHeadModel

# Set up logging
logging.basicConfig(level=logging.INFO)

# Load the tokenizer and model (this will cache them locally)
tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
model = TFGPT2LMHeadModel.from_pretrained("gpt2")

def generate_text(input_text, context=None):
    logging.info(f"Input text: {input_text}")
    if context:
        logging.info(f"Context: {context}")
        
    # Prepare the prompt with context if available
    if context:
        full_prompt = f"Context: {context}\n\nQuestion: {input_text}\n\nAnswer:"
    else:
        full_prompt = input_text
    
    logging.info(f"Full prompt: {full_prompt}")
    
    # Tokenize input
    inputs = tokenizer(full_prompt, return_tensors="tf", truncation=True, max_length=1024)

    # Generate text
    outputs = model.generate(
        **inputs,
        max_length=150,  # Reduzido para respostas mais concisas
        do_sample=True,  # Habilitar amostragem
        temperature=0.7,  # Controla aleatoriedade (0.0 = determinístico, 1.0 = mais aleatório)
        top_k=50,  # Limita as k palavras mais prováveis
        top_p=0.95,  # Nucleus sampling
        no_repeat_ngram_size=3,  # Evita repetição de trigramas
        num_return_sequences=1,  # Gerar apenas uma sequência
        pad_token_id=tokenizer.eos_token_id,
        eos_token_id=tokenizer.eos_token_id,  # Parar quando encontrar token de fim
        early_stopping=True  # Parar quando encontrar token de fim
    )

    # Log the raw output
    logging.info(f"Raw output from model: {outputs}")
    
    # Decode and print the generated text
    generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    logging.info(f"Decoded output: {generated_text}")
    
    # If we used context, try to extract just the answer part
    if context:
        try:
            answer = generated_text.split("Answer:")[-1].strip()
            return answer
        except:
            return generated_text
    
    return generated_text

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=str, required=True, help='Input text')
    parser.add_argument('--context', type=str, help='Optional context')
    
    args = parser.parse_args()
    
    output_text = generate_text(args.input, args.context)
    print(output_text)
