from flask import Flask, request, jsonify
from transformers import TFAutoModelForSequenceClassification, AutoTokenizer
import tensorflow as tf
import logging
from datetime import datetime

app = Flask(__name__)

# Configure advanced logging
logging.basicConfig(
    filename='query_logs.log',
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Load models and tokenizers
xss_model_path = './DistilBERT_fine_tuned_model'
sqli_model_path = './03042025_XSS_Classification_fine_tuned_model'

xss_tokenizer = AutoTokenizer.from_pretrained(xss_model_path)
xss_model = TFAutoModelForSequenceClassification.from_pretrained(xss_model_path)

sqli_tokenizer = AutoTokenizer.from_pretrained(sqli_model_path)
sqli_model = TFAutoModelForSequenceClassification.from_pretrained(sqli_model_path)

def log_table(title, items):
    """Helper function to create tabular log entries"""
    border = "+" + "-" * 50 + "+"
    logger.info(border)
    logger.info(f"| {title.ljust(48)} |")
    logger.info(border)
    for key, value in items:
        logger.info(f"| {key.ljust(30)} | {str(value).ljust(15)} |")
    logger.info(border + "\n")

def predict_xss(text):
    inputs = xss_tokenizer(text, return_tensors="tf", truncation=True, max_length=512)
    outputs = xss_model(**inputs)
    probs = tf.nn.softmax(outputs.logits, axis=1).numpy()[0]
    prediction = tf.argmax(outputs.logits, axis=1).numpy()[0]
    
    confidence_scores = {
        "safe": float(probs[0]),
        "malicious": float(probs[1])
    }
    
    log_table("XSS Detection Results", [
        ("Input", text),
        ("Prediction", "malicious" if prediction == 1 else "safe"),
        ("Safe Confidence", f"{confidence_scores['safe']:.4f}"),
        ("Malicious Confidence", f"{confidence_scores['malicious']:.4f}")
    ])
    
    return {
        "prediction": "malicious" if prediction == 1 else "safe",
        "confidence_scores": confidence_scores
    }

def predict_sqli(query):
    try:
        if not query:
            logger.warning("Empty query received for SQLi classification")
            return {'error': 'No query provided'}, 400

        inputs = sqli_tokenizer(
            query,
            return_tensors='tf',
            padding=True,
            truncation=True,
            max_length=512
        )
        outputs = sqli_model(**inputs)
        probs = tf.nn.softmax(outputs.logits, axis=1).numpy()[0]
        predicted_class = tf.argmax(outputs.logits, axis=1).numpy()[0]
        
        confidence_scores = {
            "non_malicious": float(probs[0]),
            "malicious": float(probs[1])
        }
        
        classification = "Malicious Query" if predicted_class == 1 else "Non-Malicious Query"
        
        log_table("SQLi Detection Results", [
            ("Query", query),
            ("Prediction", classification),
            ("Non-Malicious Confidence", f"{confidence_scores['non_malicious']:.4f}"),
            ("Malicious Confidence", f"{confidence_scores['malicious']:.4f}")
        ])
        
        return {
            "classification": classification,
            "confidence_scores": confidence_scores
        }

    except Exception as e:
        error_msg = f"SQLi Classification Error: {str(e)}"
        logger.error(error_msg)
        return {'error': error_msg}, 500

@app.route('/classify', methods=['POST'])
def classify():
    start_time = datetime.now()
    data = request.get_json()
    attack_type = data.get('type', 'unknown')
    
    logger.info(f"\n{'=' * 50}")
    logger.info(f"New Classification Request ({attack_type.upper()})")
    logger.info(f"Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Client IP: {request.remote_addr}")
    logger.info(f"{'=' * 50}")

    try:
        if attack_type == 'xss':
            user_input = data.get('user_input', '')
            if not user_input:
                logger.warning("Empty input for XSS check")
                return jsonify({'error': 'Missing user input'}), 400
            
            result = predict_xss(user_input)
            response = {
                "prediction": result["prediction"],
                "confidence_scores": result["confidence_scores"]
            }
            
            if result["prediction"] == "malicious":
                logger.warning(f"BLOCKED XSS PAYLOAD: {user_input}")

        elif attack_type == 'sqli':
            query = data.get('query', '')
            if not query:
                logger.warning("Empty query for SQLi check")
                return jsonify({'error': 'Missing query'}), 400
            
            result = predict_sqli(query)
            if isinstance(result, tuple):
                return jsonify(result[0]), result[1]
            
            response = {
                "classification": result["classification"],
                "confidence_scores": result["confidence_scores"]
            }
            
            if result["classification"] == "Malicious Query":
                logger.warning(f"BLOCKED SQLi PAYLOAD: {query}")

        else:
            logger.error(f"Invalid attack type: {attack_type}")
            return jsonify({'error': 'Invalid attack type'}), 400

        # Log processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Processing Time: {processing_time:.4f} seconds")
        
        return jsonify(response), 200

    except Exception as e:
        error_msg = f"Classification Failed: {str(e)}"
        logger.error(error_msg)
        return jsonify({'error': error_msg}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
