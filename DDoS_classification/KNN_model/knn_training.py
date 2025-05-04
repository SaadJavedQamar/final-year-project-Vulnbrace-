import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, precision_score, recall_score, f1_score
import seaborn as sns
import matplotlib.pyplot as plt
import joblib

# Load dataset
df = pd.read_csv("ddos_dataset_smote.csv")
X = df.drop(columns=["Label"])
y = df["Label"]

# Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train KNN
model = KNeighborsClassifier(n_neighbors=5)
model.fit(X_train, y_train)

# Predict & Metrics
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
precision = precision_score(y_test, y_pred)
recall = recall_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred)
cm = confusion_matrix(y_test, y_pred)

# Print Metrics
print(f"KNN Accuracy: {accuracy:.4f}")
print("Confusion Matrix:")
print(cm)

# Visualize
plt.figure(figsize=(6, 4))
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=["Normal", "DDoS"], yticklabels=["Normal", "DDoS"])
plt.title("Confusion Matrix")
plt.xlabel("Predicted")
plt.ylabel("True")
plt.show()

# Bar Plot
metrics = [precision, recall, f1]
metric_names = ['Precision', 'Recall', 'F1 Score']
plt.figure(figsize=(6, 4))
sns.barplot(x=metric_names, y=metrics, palette="Blues_d")
plt.title("Model Metrics")
plt.ylabel("Score")
plt.ylim(0, 1)
plt.show()

# Save model
joblib.dump(model, "knn_ddos_model.pkl")
print("✅ KNN model saved as knn_ddos_model.pkl")
