from transformers import DistilBertTokenizer, TFDistilBertForSequenceClassification
import tensorflow as tf
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

model_path = './03042025_XSS_Classification_fine_tuned_model'
tokenizer = DistilBertTokenizer.from_pretrained(model_path)
model = TFDistilBertForSequenceClassification.from_pretrained(model_path)

# Step 3: Define Query Classification and Evaluation Functions
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

    label_map = {0: "Non-Malicious Query", 1: "Malicious Query"}
    classification = label_map[predicted_class]

    return classification, confidence, predicted_class

def evaluate_model(test_queries, test_labels):
    predictions = []
    for query in test_queries:
        _, _, predicted_class = classify_query(query)
        predictions.append(predicted_class)

    accuracy = accuracy_score(test_labels, predictions)
    report = classification_report(test_labels, predictions, target_names=["Non-Malicious Query", "Malicious Query"], output_dict=True)
    conf_matrix = confusion_matrix(test_labels, predictions)

    print("\n--- Model Evaluation ---")
    print(f"Accuracy: {accuracy:.2f}")
    print("Classification Report:")
    print(report)
    print("Confusion Matrix:")
    print(conf_matrix)
    print("------------------------\n")

    # Plot metrics (precision, recall, f1-score) for each class (Malicious & Non-Malicious)
    metrics = ['precision', 'recall', 'f1-score']
    classes = ['Malicious Query', 'Non-Malicious Query']
    
    for metric in metrics:
        plt.figure(figsize=(8, 6))
        values = [report[classes[0]][metric], report[classes[1]][metric]]
        plt.bar(classes, values)
        plt.title(f'{metric.capitalize()} for Malicious vs Non-Malicious')
        plt.ylabel(metric.capitalize())
        plt.xlabel('Query Type')
        plt.show()

    # Plot Confusion Matrix using seaborn heatmap
    plt.figure(figsize=(6, 6))
    sns.heatmap(conf_matrix, annot=True, fmt="d", cmap='Blues', xticklabels=classes, yticklabels=classes)
    plt.title('Confusion Matrix')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.show()

    return accuracy, report, conf_matrix

# Step 4: User Interaction
if __name__ == "__main__":
    print("XSS Payload Classification - Fine-Tuned Model")
    print("Type 'exit' to quit or 'evaluate' to test the model on a dataset.\n")

    while True:
        user_query = input("Enter XSS payload to classify or type 'evaluate': ")
        if user_query.lower() == 'exit':
            print("Exiting program. Goodbye!")
            break
        elif user_query.lower() == 'evaluate':
            # Load the extreme cases dataset
            df = pd.read_csv('extreme_xss_payloads.csv')
            test_queries = df['payload'].tolist()
            test_labels = df['label'].tolist()

            # Evaluate the model on this dataset
            evaluate_model(test_queries, test_labels)
        else:
            classification, confidence, predicted_class = classify_query(user_query)
            print("\n--- Classification Result ---")
            print(f"Classification: {classification}")
            print(f"Confidence: Malicious: {confidence[1]:.2f}, Non-Malicious: {confidence[0]:.2f}")
            print("-----------------------------\n")
