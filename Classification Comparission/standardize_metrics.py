import os
import pandas as pd

def parse_metrics_file(filepath):
    filename = os.path.basename(filepath).lower()
    task = 'SQLi' if 'sqli' in filename else 'XSS'
    model_name = filename.replace('_metrics.csv', '').replace('_metrics.txt', '').lower()

    try:
        if filename.endswith('.csv'):
            # First, try reading as headered CSV
            df = pd.read_csv(filepath)

            df.columns = [col.strip().lower() for col in df.columns]  # Normalize headers

            # Case 1: Standard header row (e.g., Accuracy, F1, AUC)
            if 'accuracy' in df.columns and ('f1' in df.columns or 'f1 score' in df.columns):
                acc_col = 'accuracy'
                f1_col = 'f1' if 'f1' in df.columns else 'f1 score'
                acc = float(df[acc_col].values[0])
                f1 = float(df[f1_col].values[0])
                return model_name, task, acc, f1

            # Case 2: Vertical format with two columns
            if df.shape[1] == 2:
                df.columns = ['Metric', 'Value']
                df['Metric'] = df['Metric'].astype(str).str.strip().str.lower()
                acc_row = df[df['Metric'] == 'accuracy']
                f1_row = df[df['Metric'] == 'f1']
                if not acc_row.empty and not f1_row.empty:
                    acc = float(acc_row['Value'].values[0])
                    f1 = float(f1_row['Value'].values[0])
                    return model_name, task, acc, f1

            # Case 3: XSS DistilBERT special format
            if 'metric' in df.columns and 'overall accuracy' in df.columns:
                acc = float(df['overall accuracy'].values[0])
                f1 = float(df['malicious f1'].values[0])
                return model_name, task, acc, f1

        elif filename.endswith('.txt'):
            with open(filepath, 'r') as f:
                lines = f.readlines()
            acc = None
            f1 = None
            for line in lines:
                if 'Accuracy' in line:
                    acc = float(line.split(':')[-1].strip())
                elif 'F1' in line and 'Score' in line:
                    f1 = float(line.split(':')[-1].strip())
            if acc is not None and f1 is not None:
                return model_name, task, acc, f1

    except Exception as e:
        print(f"[INFO] Could not parse: {filename}")
    return None


def standardize_all_metrics(metrics_dir='metrics'):
    """
    Loop through the given directory and standardize all metrics files into a DataFrame.
    """
    data = []
    for fname in os.listdir(metrics_dir):
        if fname.endswith('.csv') or fname.endswith('.txt'):
            full_path = os.path.join(metrics_dir, fname)
            parsed = parse_metrics_file(full_path)
            if parsed:
                data.append(parsed)
            else:
                print(f"[INFO] Could not parse: {fname}")

    if not data:
        print("[ERROR] No valid metrics parsed. Check formatting or paths.")
        return pd.DataFrame(columns=['model_name', 'task', 'accuracy', 'f1_score'])

    df = pd.DataFrame(data, columns=['model_name', 'task', 'accuracy', 'f1_score'])
    df.sort_values(by=['task', 'accuracy'], ascending=False, inplace=True)
    return df

# === Entry Point ===
if __name__ == "__main__":
    metrics_folder = r"F:\10032025 FYP2\Classification Comparission\metrics"
    final_df = standardize_all_metrics(metrics_folder)
    print(final_df)
    
    output_path = os.path.join(metrics_folder, "..", "standardized_metrics.csv")
    final_df.to_csv(output_path, index=False)
    print(f"[INFO] Saved: {output_path}")
