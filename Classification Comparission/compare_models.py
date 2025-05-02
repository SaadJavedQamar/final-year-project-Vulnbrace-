import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load standardized metrics
metrics_df = pd.read_csv("standardized_metrics.csv")

# Set seaborn style
sns.set(style="whitegrid")

# Filter to only specific models
keep_models = ['distilbert', 'nb', 'knn', 'qda']
metrics_df = metrics_df[metrics_df['model_name'].str.lower().str.contains('|'.join(keep_models))]

# Pretty model names mapping
name_map = {
    'sqli_distilbert': 'DistilBERT (SQLi)',
    'sqli_nb': 'Naive Bayes (SQLi)',
    'sqli_knn': 'KNN (SQLi)',
    'sqli_qda': 'QDA (SQLi)',
    'xss_distilbert': 'DistilBERT (XSS)',
    'xss_nb': 'Naive Bayes (XSS)',
    'xss_knn': 'KNN (XSS)',
    'xss_qda': 'QDA (XSS)'
}
metrics_df['pretty_name'] = metrics_df['model_name'].map(name_map)

# Define custom colors: DistilBERT in a unique color
def get_palette(names):
    return ['#FF6F61' if 'DistilBERT' in name else '#6BAED6' for name in names]

# Plotting function
def plot_metric(df, metric, title, filename):
    plt.figure(figsize=(10, 6))
    colors = get_palette(df['pretty_name'].tolist())
    ax = sns.barplot(
        x='pretty_name', 
        y=metric, 
        data=df, 
        palette=colors
    )
    ax.set_title(title, fontsize=14)
    ax.set_ylabel(metric.replace("_", " ").title(), fontsize=12)
    ax.set_xlabel("Model", fontsize=12)
    plt.xticks(rotation=30, ha='right')
    plt.ylim(0, 1.1)
    plt.tight_layout()
    plt.savefig(filename, dpi=300)
    plt.show()

# Split by task and plot separately
for task in ['SQLi', 'XSS']:
    task_df = metrics_df[metrics_df['task'] == task]
    plot_metric(task_df, 'accuracy', f'{task} - Accuracy Comparison', f'{task.lower()}_accuracy_comparison.png')
    plot_metric(task_df, 'f1_score', f'{task} - F1 Score Comparison', f'{task.lower()}_f1_comparison.png')
