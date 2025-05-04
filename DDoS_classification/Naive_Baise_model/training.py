# train_naive_bayes_model.py

import pandas as pd
import numpy as np
import pickle
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import GaussianNB
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

# Load SMOTE dataset
df_smote = pd.read_csv("ddos_dataset_smote.csv")

# Separate features and target
X = df_smote.drop(columns=["Label"])
y = df_smote["Label"]

# Train/Test Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Initialize Naive Bayes Classifier
nb_model = GaussianNB()

# Train the model
nb_model.fit(X_train, y_train)

# Predict on test data
y_pred = nb_model.predict(X_test)

# Evaluation Metrics
accuracy = accuracy_score(y_test, y_pred)
precision = precision_score(y_test, y_pred)
recall = recall_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred)
cm = confusion_matrix(y_test, y_pred)

print(f"Naive Bayes Accuracy: {accuracy:.4f}")
print("Confusion Matrix:")
print(cm)

# Confusion Matrix (Raw)
plt.figure(figsize=(6, 5))
sns.heatmap(cm, annot=True, fmt="d", cmap="Purples", xticklabels=["Normal", "DDoS"], yticklabels=["Normal", "DDoS"])
plt.title("Confusion Matrix (Raw Values)")
plt.xlabel("Predicted")
plt.ylabel("True")
plt.show()

# Normalized Confusion Matrix
cm_normalized = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
plt.figure(figsize=(6, 5))
sns.heatmap(cm_normalized, annot=True, fmt=".2f", cmap="Purples", xticklabels=["Normal", "DDoS"], yticklabels=["Normal", "DDoS"])
plt.title("Normalized Confusion Matrix")
plt.xlabel("Predicted")
plt.ylabel("True")
plt.show()

# Precision, Recall, F1 Bar Plot
metrics = [precision, recall, f1]
metrics_names = ['Precision', 'Recall', 'F1 Score']

plt.figure(figsize=(6, 4))
sns.barplot(x=metrics_names, y=metrics, palette="Purples_d")
plt.title("Precision, Recall, and F1 Scores")
plt.ylabel("Score")
plt.show()

# Save the model using pickle
with open("naive_bayes_ddos_model.pkl", "wb") as f:
    pickle.dump(nb_model, f)
print("Model saved successfully as naive_bayes_ddos_model.pkl")
