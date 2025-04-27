import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pycaret.classification import *

def parse_model_selection(input_str, max_models):
    selected_indices = []
    parts = input_str.replace(' ', '').split(',')
    for part in parts:
        if '-' in part:
            start, end = map(int, part.split('-'))
            selected_indices.extend(range(start, end+1))
        else:
            selected_indices.append(int(part))
    return [i for i in selected_indices if 0 <= i < max_models]

# Step 1: Load dataset
df = pd.read_csv('balanced_XSS_dataset.csv')
df = df[['Sentence', 'Label']]

# Step 2: Check for null values
print("\nNull values check:")
print(df.isnull().sum())

# Step 3: Initialize setup
exp = setup(data=df,
            target='Label',
            session_id=123,
            verbose=True,
            html=False,
            log_experiment=False,
            text_features=['Sentence'])

# Step 4: Compare all models
print("\nComparing all models...")
best_model = compare_models(sort='Accuracy')
compare_df = pull().reset_index()

# Sort by ascending accuracy
compare_df = compare_df.sort_values('Accuracy', ascending=True).reset_index(drop=True)

# Step 5: Display model accuracies and get selection
print("\nModel Accuracies:")
display_df = compare_df[['Model', 'Accuracy', 'F1', 'AUC']]
display_df.index += 1
print(display_df.to_string())

while True:
    try:
        selection = input("\nEnter models to save (e.g., '1-3,5,7-9' or 'all'): ")
        if selection.lower() == 'all':
            selected_indices = list(range(len(compare_df)))
            break
        else:
            selected_indices = parse_model_selection(selection, len(compare_df))
            if selected_indices:
                break
            print("Invalid selection. Please try again.")
    except:
        print("Invalid input format. Please try again.")

# Convert to 0-based indices
selected_indices = [i-1 for i in selected_indices]
selected_models = compare_df.iloc[selected_indices]

# Step 6: Create model reference mapping
models_df = models()
print("\nAvailable model columns:", models_df.columns.tolist())  # Debug output

# Create manual model ID mapping based on PyCaret's current naming
model_id_map = {
    'Linear Discriminant Analysis': 'lda',
    'Quadratic Discriminant Analysis': 'qda',
    'Dummy Classifier': 'dummy',
    'Naive Bayes': 'nb',
    'K Neighbors Classifier': 'knn',
    'Logistic Regression': 'lr',
    'Gradient Boosting Classifier': 'gbc',
    'Decision Tree Classifier': 'dt',
    'CatBoost Classifier': 'catboost',
    'Extreme Gradient Boosting': 'xgboost',
    'Ada Boost Classifier': 'ada',
    'Ridge Classifier': 'ridge',
    'Light Gradient Boosting Machine': 'lightgbm',
    'Random Forest Classifier': 'rf',
    'SVM - Linear Kernel': 'svm',
    'Extra Trees Classifier': 'et'
}

print(f"\nProcessing {len(selected_models)} models...")
for idx, row in selected_models.iterrows():
    model_name = row['Model']
    model_id = model_id_map.get(model_name)
    
    if not model_id:
        print(f"⚠️ Skipping {model_name} - no ID mapping found")
        continue
        
    try:
        print(f"\n--- Processing {model_name} ({idx+1}/{len(selected_models)}) ---")
        
        # Create and save model
        model = create_model(model_id, verbose=False)
        save_model(model, f'XSS_{model_id}_model')
        
        # Generate confusion matrix
        plot_model(model, plot='confusion_matrix', save=True,
                 plot_kwargs={'title': f'{model_name} Confusion Matrix'},
                 verbose=False)
        
        # Save metrics
        with open(f'XSS_{model_id}_metrics.txt', 'w') as f:
            f.write(f"Model: {model_name}\n")
            f.write(f"Accuracy: {row['Accuracy']:.4f}\n")
            f.write(f"F1 Score: {row['F1']:.4f}\n")
            f.write(f"AUC: {row['AUC']:.4f}\n")
        
        print(f"✅ Success: {model_name} processed")
        
    except Exception as e:
        print(f"❌ Error processing {model_name}: {str(e)}")
        continue

# Step 7: Generate comparison plot
plt.figure(figsize=(12, 6))
n_models = len(selected_models)
x = np.arange(n_models)
width = 0.3

plt.bar(x - width/2, selected_models['Accuracy'], width, label='Accuracy')
plt.bar(x + width/2, selected_models['F1'], width, label='F1 Score', alpha=0.7)

plt.xticks(x, selected_models['Model'], rotation=45, ha='right')
plt.title('Selected Models Performance', fontsize=14)
plt.ylabel('Scores', fontsize=12)
plt.ylim(0, 1.05)
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig('selected_models_comparison.png', dpi=300, bbox_inches='tight')
plt.close()

print("\n✅ Processing complete!")
print(f"Saved artifacts for {len(selected_models)} models:")
print("- Comparison plot: selected_models_comparison.png")
print("- Models: XSS_*_model.pkl")
print("- Confusion matrices: ConfusionMatrix*.png")
print("- Metrics files: XSS_*_metrics.txt")