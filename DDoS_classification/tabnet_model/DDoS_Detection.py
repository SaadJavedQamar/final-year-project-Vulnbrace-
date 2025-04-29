# detect_ddos_tabnet.py
import pandas as pd
import numpy as np
from pytorch_tabnet.tab_model import TabNetClassifier

# Load traffic summary
df = pd.read_csv("traffic_log_for_detection.csv")

# Load TabNet model
tabnet_model = TabNetClassifier()
tabnet_model.load_model("tabnet_ddos_model.zip")

# Predict
prediction = tabnet_model.predict(df.values)

# Output result
if prediction[0] == 1:
    print("🚨 DDoS Detected based on TabNet model.")
else:
    print("✅ Normal Traffic detected.")
