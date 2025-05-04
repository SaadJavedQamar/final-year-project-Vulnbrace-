import pandas as pd
import numpy as np
import torch
from pytorch_tabnet.tab_model import TabNetClassifier
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import seaborn as sns
import matplotlib.pyplot as plt
import joblib
import pickle

# Load Dataset
data = pd.read_csv("ddos_dataset_smote.csv")
X = data.drop(columns=["Label"])
y = data["Label"]

# Train/Test Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Metrics Storage
results = {}

# TabNet Model
print("Training TabNet Model...")
torch.manual_seed(42)
np.random.seed(42)
tabnet_model = TabNetClassifier()
tabnet_model.fit(X_train.values, y_train.values, eval_set=[(X_test.values, y_test.values)], max_epochs=7, patience=12)
y_pred_tabnet = tabnet_model.predict(X_test.values)

results["TabNet"] = {
    "Accuracy": accuracy_score(y_test, y_pred_tabnet),
    "Precision": precision_score(y_test, y_pred_tabnet),
    "Recall": recall_score(y_test, y_pred_tabnet),
    "F1": f1_score(y_test, y_pred_tabnet),
    "Confusion Matrix": confusion_matrix(y_test, y_pred_tabnet)
}
tabnet_model.save_model("tabnet_ddos_model.zip")

# Naive Bayes Model
print("Training Naive Bayes Model...")
nb_model = GaussianNB()
nb_model.fit(X_train, y_train)
y_pred_nb = nb_model.predict(X_test)

results["Naive Bayes"] = {
    "Accuracy": accuracy_score(y_test, y_pred_nb),
    "Precision": precision_score(y_test, y_pred_nb),
    "Recall": recall_score(y_test, y_pred_nb),
    "F1": f1_score(y_test, y_pred_nb),
    "Confusion Matrix": confusion_matrix(y_test, y_pred_nb)
}
with open("naive_bayes_ddos_model.pkl", "wb") as f:
    pickle.dump(nb_model, f)

# KNN Model
print("Training KNN Model...")
knn_model = KNeighborsClassifier(n_neighbors=5)
knn_model.fit(X_train, y_train)
y_pred_knn = knn_model.predict(X_test)

results["KNN"] = {
    "Accuracy": accuracy_score(y_test, y_pred_knn),
    "Precision": precision_score(y_test, y_pred_knn),
    "Recall": recall_score(y_test, y_pred_knn),
    "F1": f1_score(y_test, y_pred_knn),
    "Confusion Matrix": confusion_matrix(y_test, y_pred_knn)
}
joblib.dump(knn_model, "knn_ddos_model.pkl")

# Visualization
print("Generating Visualizations...")

# Plot for each metric
metrics = ["Accuracy", "Precision", "Recall", "F1"]
for metric in metrics:
    plt.figure(figsize=(8, 5))
    plt.bar(results.keys(), [results[model][metric] for model in results], color=['blue', 'green', 'orange'])
    plt.title(f"{metric} Comparison Across Models")
    plt.ylabel(metric)
    plt.xlabel("Models")
    plt.savefig(f"{metric.lower()}_comparison.png")
    plt.show()

# Confusion Matrices
for model, result in results.items():
    cm = result["Confusion Matrix"]
    plt.figure(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=["Normal", "DDoS"], yticklabels=["Normal", "DDoS"])
    plt.title(f"Confusion Matrix - {model}")
    plt.xlabel("Predicted")
    plt.ylabel("True")
    plt.savefig(f"confusion_matrix_{model.lower()}.png")
    plt.show()

print("All models trained and visualizations saved.")
