import sys
import logging
from transformers import GPT2Tokenizer, TFGPT2LMHeadModel

# Set up logging
logging.basicConfig(level=logging.INFO)

# Load the tokenizer and model (this will cache them locally)
tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
model = TFGPT2LMHeadModel.from_pretrained("gpt2")

def generate_text(input_text):
    logging.info(f"Input text: {input_text}")
    
    # Tokenize input
    inputs = tokenizer(input_text, return_tensors="tf")

    # Generate text
    outputs = model.generate(**inputs, max_length=30, temperature=0.7, top_k=50)

    # Log the raw output
    logging.info(f"Raw output from model: {outputs}")
    
    # Decode and print the generated text
    generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    logging.info(f"Decoded output: {generated_text}")
    return generated_text

# Check if a command-line argument was provided
if len(sys.argv) > 1:
    input_text = sys.argv[1]  # Use the first argument as input text
else:
    input_text = "Greet me!"
    
output_text = generate_text(input_text)
print(output_text)
