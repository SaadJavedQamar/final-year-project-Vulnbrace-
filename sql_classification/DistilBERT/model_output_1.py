from transformers import DistilBertTokenizer, TFDistilBertForSequenceClassification
import tensorflow as tf
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, precision_score, recall_score, f1_score
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Load the saved fine-tuned model and tokenizer
model_path = './DistilBERT_fine_tuned_model'
tokenizer = DistilBertTokenizer.from_pretrained(model_path)
model = TFDistilBertForSequenceClassification.from_pretrained(model_path)

# Function to classify a single SQL query
def classify_query(query):
    inputs = tokenizer(
        query,
        return_tensors='tf',
        padding=True,
        truncation=True,
        max_length=512
    )
    outputs = model(inputs)
    logits = outputs.logits
    confidence = tf.nn.softmax(logits, axis=1).numpy()[0]
    predicted_class = tf.argmax(logits, axis=1).numpy()[0]

    return predicted_class, confidence

# Function to plot confusion matrix
def plot_confusion_matrix(conf_matrix, class_names):
    plt.figure(figsize=(6, 6))
    sns.heatmap(conf_matrix, annot=True, fmt='d', cmap='Blues', xticklabels=class_names, yticklabels=class_names)
    plt.xlabel('Predicted Labels')
    plt.ylabel('True Labels')
    plt.title('Confusion Matrix')
    plt.show()

# Function to plot metrics
def plot_metrics(metrics):
    metric_names = list(metrics.keys())
    metric_values = list(metrics.values())

    plt.figure(figsize=(8, 5))
    plt.bar(metric_names, metric_values, color='skyblue')
    plt.ylim(0, 1)  # Metrics are between 0 and 1
    plt.title('Model Performance Metrics')
    plt.ylabel('Score')
    plt.xlabel('Metrics')
    plt.show()

# Function to evaluate the model and visualize results
def evaluate_and_visualize(test_queries, test_labels):
    predictions = []
    for query in test_queries:
        predicted_class, _ = classify_query(query)
        predictions.append(predicted_class)
    
    # Calculate metrics
    accuracy = accuracy_score(test_labels, predictions)
    precision = precision_score(test_labels, predictions)
    recall = recall_score(test_labels, predictions)
    f1 = f1_score(test_labels, predictions)
    conf_matrix = confusion_matrix(test_labels, predictions)

    # Print evaluation results
    print("\n--- Model Evaluation ---")
    print(f"Accuracy: {accuracy:.2f}")
    print(f"Precision: {precision:.2f}")
    print(f"Recall: {recall:.2f}")
    print(f"F1 Score: {f1:.2f}")
    print("Confusion Matrix:")
    print(conf_matrix)
    print("------------------------\n")

    # Visualize metrics
    metrics = {
        'Accuracy': accuracy,
        'Precision': precision,
        'Recall': recall,
        'F1 Score': f1
    }
    plot_metrics(metrics)
    plot_confusion_matrix(conf_matrix, ["Non-Malicious Query", "Malicious Query"])

# Main function to interact with the user or evaluate on a dataset
if __name__ == "__main__":
    print("SQL Query Classification - Fine-Tuned Model")
    print("Type 'evaluate' to test a dataset, or type 'exit' to quit.\n")

    while True:
        user_input = input("Enter an SQL query to classify (or type 'evaluate' or 'exit'): ").strip()
        
        if user_input.lower() == "exit":
            print("Exiting the program. Goodbye!")
            break
        elif user_input.lower() == "evaluate":
            # Example test dataset (replace with your own)
            test_queries = [
                "SELECT * FROM users WHERE id = 1",  # Non-Malicious
                "SELECT username, password FROM users; DROP TABLE users;",  # Malicious
                "INSERT INTO logs VALUES (1, 'test', 'success')",  # Non-Malicious
                "' OR '1'='1",  # Malicious
                "SELECT employee_id, last_name, first_name, salary, RANK() OVER (ORDER BY salary DESC) as ranking FROM employee ORDER BY ranking",  # Non-Malicious
                "replace",  # Malicious
                "(or type 'evaluate' or 'exit'): SELECT * FROM users WHERE id = 1",  # Malicious
                "#NAME?",  # Malicious
            ]
            test_labels = [0, 1, 0, 1, 0, 1, 1, 1]  # True labels
            evaluate_and_visualize(test_queries, test_labels)
        else:
            # Classify user input
            predicted_class, confidence = classify_query(user_input)
            label_map = {0: "Non-Malicious Query", 1: "Malicious Query"}
            classification = label_map[predicted_class]
            print("\n--- Classification Result ---")
            print(f"Query: {user_input}")
            print(f"Classification: {classification}")
            print(f"Confidence Scores: Non-Malicious: {confidence[0]:.2f}, Malicious: {confidence[1]:.2f}")
            print("-----------------------------\n")
