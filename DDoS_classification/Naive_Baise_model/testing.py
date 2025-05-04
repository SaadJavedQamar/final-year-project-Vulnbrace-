# test_naive_bayes_model.py

import pandas as pd
import pickle

# Load the trained model
with open("naive_bayes_ddos_model.pkl", "rb") as f:
    model = pickle.load(f)

# Take user input
print("Please enter the following traffic data:")
request_rate = float(input("Request Rate: "))
payload_size = float(input("Payload Size: "))
unique_ips = float(input("Unique IPs: "))

# Create DataFrame from input
input_data = {
    "Request Rate": request_rate,
    "Payload Size": payload_size,
    "Unique IPs": unique_ips
}
input_df = pd.DataFrame([input_data])

# Predict using model
prediction = model.predict(input_df)

# Output result
if prediction[0] == 1:
    print("🚨 The traffic is DDoS.")
else:
    print("✅ Normal Traffic.")
