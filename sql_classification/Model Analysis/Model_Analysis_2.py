import pandas as pd
import re
import matplotlib.pyplot as plt
import numpy as np
from pycaret.classification import *
import warnings
warnings.filterwarnings('ignore')

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

# Step 1: Load and preprocess SQLi data
def preprocess_sql(query):
    """Simplify SQL patterns while preserving injection characteristics"""
    query = query.lower()
    query = re.sub(r'\b(select|union|sleep|where|and|or|exec)\b', 'sql_keyword', query)
    query = re.sub(r'\d+', 'num', query)
    query = re.sub(r'[;\'\(\)#-]', 'special_char', query)
    return query.strip()

df = pd.read_csv('balanced_SQL_dataset.csv')
df['Query'] = df['Query'].apply(preprocess_sql)
df = df[['Query', 'Label']]

# Step 2: Check for null values
print("\nNull values check:")
print(df.isnull().sum())

# Step 3: Optimized setup for SQLi
exp = setup(
    data=df,
    target='Label',
    session_id=123,
    verbose=True,
    html=False,
    log_experiment=False,
    text_features=['Query'],
    text_features_method='tf-idf',
    fold_strategy='stratifiedkfold',
    fold=3,
    n_jobs=1
)

# Step 4: Compare models with error handling
print("\nComparing SQLi models...")
try:
    best_model = compare_models(
        include=['lda', 'qda', 'lr', 'svm', 'nb', 'rf', 'et', 'xgboost', 'lightgbm', 'ada', 'ridge', 'knn'],
        sort='Accuracy',
        errors='ignore'
    )
    compare_df = pull().reset_index()
except Exception as e:
    print(f"Comparison error: {str(e)}")
    compare_df = pd.DataFrame()

if not compare_df.empty:
    compare_df = compare_df.sort_values('Accuracy', ascending=True).reset_index(drop=True)
    print("\nSQLi Model Accuracies:")
    display_df = compare_df[['Model', 'Accuracy', 'F1', 'AUC']]
    display_df.index += 1
    print(display_df.to_string())
else:
    print("No models could be compared successfully")
    exit()

# Model selection
selected_indices = []
while True:
    try:
        selection = input("\nEnter models to save (e.g., '1-3,5' or 'all'): ").strip()
        if selection.lower() == 'all':
            selected_indices = list(range(len(compare_df)))
            break
        selected_indices = parse_model_selection(selection, len(compare_df))
        if selected_indices:
            break
        print("Invalid selection. Try again.")
    except Exception as e:
        print(f"Input error: {str(e)}")

selected_indices = [i-1 for i in selected_indices if i > 0]
selected_models = compare_df.iloc[selected_indices]

# Model processing with enhanced logging
model_id_map = {
    'Linear Discriminant Analysis': 'lda',
    'Quadratic Discriminant Analysis': 'qda',
    'Logistic Regression': 'lr',
    'SVM - Linear Kernel': 'svm',
    'Naive Bayes': 'nb',
    'Random Forest Classifier': 'rf',
    'Extra Trees Classifier': 'et',
    'Extreme Gradient Boosting': 'xgboost',
    'Light Gradient Boosting Machine': 'lightgbm',
    'Ada Boost Classifier': 'ada',
    'Ridge Classifier': 'ridge',
    'K Neighbors Classifier': 'knn'
}

print(f"\nProcessing {len(selected_models)} models:")
for idx, row in selected_models.iterrows():
    model_name = row['Model']
    model_id = model_id_map.get(model_name)
    
    if not model_id:
        print(f"Skipping {model_name} - no mapping")
        continue
        
    try:
        print(f"\n[{idx+1}/{len(selected_models)}] Training {model_name}")
        
        # Create and save model
        model = create_model(model_id, verbose=False)
        save_model(model, f'SQLi_{model_id}')
        
        # Generate evaluation plots
        plot_model(model, 'confusion_matrix', save=True, verbose=False)
        
        # Save metrics
        metrics = {
            'Accuracy': row['Accuracy'],
            'F1': row['F1'],
            'AUC': row['AUC']
        }
        pd.DataFrame(metrics.items()).to_csv(f'SQLi_{model_id}_metrics.csv')
        
        print(f"✅ Saved {model_id} successfully")
        
    except Exception as e:
        print(f"❌ Failed {model_name}: {str(e)}")

# Visualization
try:
    plt.figure(figsize=(12, 6))
    selected_models.plot(x='Model', y=['Accuracy', 'F1'], kind='bar')
    plt.title('SQLi Detection Performance', fontsize=14)
    plt.ylabel('Scores')
    plt.ylim(0.5, 1.0)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('sqli_performance.png', dpi=150)
    plt.close()
except Exception as e:
    print(f"Visualization error: {str(e)}")

print("\n✅ Process completed!")
print("Generated artifacts:")
print("- sqli_performance.png")
print("- SQLi_*.pkl models")
print("- SQLi_*_metrics.csv")
print("- ConfusionMatrix*.png")