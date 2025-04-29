# ddos_simulator.py
import requests
import random
import time

# Config
url = "http://localhost:8080/shopping/"
total_requests = 100

# Simulated input ranges
payload_size_range = (1, 10)         # KB
unique_ips_pool = [f"192.168.1.{i}" for i in range(1, 50)]  # Simulated unique IPs

# For collecting traffic data
traffic_logs = []

start_time = time.time()

for i in range(total_requests):
    # Simulate a delay (optional)
    # time.sleep(0.1)

    try:
        response = requests.get(url)
        status = response.status_code
    except Exception as e:
        status = 0  # Treat connection error as 0

    payload_size = random.uniform(*payload_size_range)  # Fake payload
    src_ip = random.choice(unique_ips_pool)

    traffic_logs.append({
        "Request Rate": None,  # To be calculated later
        "Payload Size": payload_size,
        "Unique IPs": src_ip
    })

    print(f"Request {i+1}: Status {status}, IP {src_ip}, Payload {payload_size:.2f} KB")

end_time = time.time()

# Calculate request rate
total_duration = end_time - start_time
request_rate = total_requests / total_duration

# Assign request rate and calculate number of unique IPs
unique_ip_count = len(set([log["Unique IPs"] for log in traffic_logs]))

# Average payload
avg_payload = sum([log["Payload Size"] for log in traffic_logs]) / len(traffic_logs)

# Prepare final traffic summary for model
traffic_summary = {
    "Request Rate": request_rate,
    "Payload Size": avg_payload,
    "Unique IPs": unique_ip_count
}

# Save to CSV or directly pass to model
import pandas as pd
df = pd.DataFrame([traffic_summary])
df.to_csv("traffic_log_for_detection.csv", index=False)

print("\nTraffic summary exported to traffic_log_for_detection.csv")
