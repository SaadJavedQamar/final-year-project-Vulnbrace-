from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
import os
from flask import Flask, request, jsonify, send_file
from transformers import TFAutoModelForSequenceClassification, AutoTokenizer
import tensorflow as tf
import pandas as pd
from pytorch_tabnet.tab_model import TabNetClassifier
import logging
from datetime import datetime
import uuid
import json
import textwrap
import re


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

def log_block(title, content_dict):
    border = "#" * 80
    block_lines = [border]
    block_lines.append(f"# {title.center(76)} #")
    block_lines.append(border)

    for key, value in content_dict.items():
        if isinstance(value, dict):
            value = json.dumps(value, indent=None, separators=(', ', ': '))
        # Wrap long values
        if len(str(value)) > 60:
            wrapped = textwrap.wrap(str(value), width=60)
            block_lines.append(f"{key:<24}: {wrapped[0]}")
            for line in wrapped[1:]:
                block_lines.append(f"{'':<26}{line}")
        else:
            block_lines.append(f"{key:<24}: {value}")

    block_lines.append(border)
    return "\n" + "\n".join(block_lines) + "\n"



def predict_xss(text):
    inputs = xss_tokenizer(text, return_tensors="tf", truncation=True, max_length=512)
    outputs = xss_model(**inputs)
    probs = tf.nn.softmax(outputs.logits, axis=1).numpy()[0]
    prediction = tf.argmax(outputs.logits, axis=1).numpy()[0]

    confidence_scores = {
        "safe": round(float(probs[0]), 4),
        "malicious": round(float(probs[1]), 4)
    }

    log_text = log_block("XSS Detection Results", {
        "Input": text,
        "Prediction": "malicious" if prediction == 1 else "safe",
        "Confidence Scores": confidence_scores
    })
    logger.info(log_text)

    return {
        "prediction": "malicious" if prediction == 1 else "safe",
        "confidence_scores": confidence_scores
    }


def predict_sqli(query):
    try:
        if not query:
            logger.warning("Empty query received for SQLi classification")
            return {'error': 'No query provided'}, 400

        inputs = sqli_tokenizer(query, return_tensors='tf', padding=True, truncation=True, max_length=512)
        outputs = sqli_model(**inputs)
        probs = tf.nn.softmax(outputs.logits, axis=1).numpy()[0]
        predicted_class = tf.argmax(outputs.logits, axis=1).numpy()[0]

        confidence_scores = {
            "non_malicious": round(float(probs[0]), 4),
            "malicious": round(float(probs[1]), 4)
        }

        classification = "Malicious Query" if predicted_class == 1 else "Non-Malicious Query"

        log_text = log_block("SQLi Detection Results", {
            "Query": query,
            "Prediction": classification,
            "Confidence Scores": confidence_scores
        })
        logger.info(log_text)

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
    request_id = str(uuid.uuid4())[:8]  # Short unique ID
    data = request.get_json()
    attack_type = data.get('type', 'unknown').lower()

    logger.info(f"\n{'=' * 70}")
    logger.info(f"Request ID      : {request_id}")
    logger.info(f"Classification  : {attack_type.upper()}")
    logger.info(f"Start Time      : {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Client IP       : {request.remote_addr}")
    logger.info(f"{'=' * 70}")

    try:
        if attack_type == 'xss':
            user_input = data.get('user_input', '')
            if not user_input:
                logger.warning(f"[{request_id}] Empty input for XSS check")
                return jsonify({'error': 'Missing user input'}), 400

            result = predict_xss(user_input)
            response = {
                "request_id": request_id,
                "prediction": result["prediction"],
                "confidence_scores": result["confidence_scores"]
            }

            if result["prediction"] == "malicious":
                logger.warning(f"[{request_id}] BLOCKED XSS PAYLOAD: {user_input}")

        elif attack_type == 'sqli':
            query = data.get('query', '')
            if not query:
                logger.warning(f"[{request_id}] Empty query for SQLi check")
                return jsonify({'error': 'Missing query'}), 400

            result = predict_sqli(query)
            if isinstance(result, tuple):  # Error occurred
                return jsonify(result[0]), result[1]

            response = {
                "request_id": request_id,
                "classification": result["classification"],
                "confidence_scores": result["confidence_scores"]
            }

            if result["classification"] == "Malicious Query":
                logger.warning(f"[{request_id}] BLOCKED SQLi PAYLOAD: {query}")

        else:
            logger.error(f"[{request_id}] Invalid attack type: {attack_type}")
            return jsonify({'error': 'Invalid attack type'}), 400

        processing_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Processing Time : {processing_time:.4f} seconds")
        logger.info(f"{'-' * 70}\n")

        return jsonify(response), 200

    except Exception as e:
        error_msg = f"[{request_id}] Classification Failed: {str(e)}"
        logger.error(error_msg)
        return jsonify({'error': error_msg}), 500


def run_ddos_detection_once():
    try:
        df = pd.read_csv("traffic_log_for_detection.csv")
        tabnet_model = TabNetClassifier()
        tabnet_model.load_model("tabnet_ddos_model.zip")
        prediction = tabnet_model.predict(df.values)
        result = "DDoS Detected" if prediction[0] == 1 else "Normal Traffic"

        log_text = log_block("DDoS Detection Result", {
            "Status": result
        })
        logger.info(log_text)

    except Exception as e:
        logger.error(f"DDoS Detection Failed: {str(e)}")
        
        
@app.route('/generate_report', methods=['GET'])
def generate_report():
    try:
        doc = Document()
        doc.add_heading("Vulnerability Assessment Report", 0)

        doc.add_paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        doc.add_paragraph("Generated by: VULNBRACE Security Engine")
        doc.add_paragraph("")

        sections = {
            "XSS Detection Results": [],
            "SQLi Detection Results": [],
            "DDoS Detection Result": [],
        }

        def clean_line(line):
            return ''.join(ch for ch in line if ch.isprintable())

        log_path = "/home/atifali/Desktop/SQL Classification/query_logs.log"
        if not os.path.exists(log_path):
            raise FileNotFoundError(f"Log file not found: {log_path}")

        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = [clean_line(line) for line in f]

        current_section = None
        for line in lines:
            if "XSS Detection Results" in line:
                current_section = "XSS Detection Results"
            elif "SQLi Detection Results" in line:
                current_section = "SQLi Detection Results"
            elif "DDoS Detection Result" in line:
                current_section = "DDoS Detection Result"

            if current_section and line.strip():
                sections[current_section].append(line.strip())

        for section, content in sections.items():
            if content:
                doc.add_heading(section, level=1)
                for line in content:
                    p = doc.add_paragraph()
                    run = p.add_run(line)
                    run.font.size = Pt(10)

                    if "BLOCKED" in line or "malicious" in line.lower():
                        run.font.color.rgb = RGBColor(255, 0, 0)
                    elif "safe" in line.lower() or "non-malicious" in line.lower():
                        run.font.color.rgb = RGBColor(0, 128, 0)
                    elif "DDoS" in line:
                        run.font.color.rgb = RGBColor(0, 0, 255)

                doc.add_paragraph("\n")

        report_path = "vulnerability_report.docx"
        doc.save(report_path)
        return send_file(report_path, as_attachment=True)

    except Exception as e:
        logging.error(f"Report generation failed: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    run_ddos_detection_once()
    app.run(host='0.0.0.0', port=5000)
