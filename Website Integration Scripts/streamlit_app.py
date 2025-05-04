import streamlit as st
import pandas as pd
import os
import re
from datetime import datetime
import matplotlib.pyplot as plt
from docx import Document
from io import BytesIO

# Parse logs
def parse_logs(log_path='query_logs.log'):
    if not os.path.exists(log_path):
        return []

    with open(log_path, 'r') as file:
        lines = file.readlines()

    entries = []
    current = {}
    for line in lines:
        line = line.strip()
        if "Request ID" in line:
            if current:
                entries.append(current)
            current = {"timestamp": line[:19].strip()}
        elif "Classification" in line:
            current["type"] = line.split(":")[-1].strip()
        elif "Prediction" in line or "classification" in line:
            result_part = line.split(":")[-1].strip()
            current["result"] = result_part
            # Extract confidence if exists
            match = re.search(r'\((\d+)%', result_part)
            if match:
                current["confidence"] = int(match.group(1))
        elif "Query" in line or "Input" in line:
            current["payload"] = line.split(":", 1)[-1].strip()
        elif "BLOCKED" in line:
            current["blocked"] = True
        elif "DDoS Detected" in line:
            entries.append({
                "timestamp": line[:19].strip(),
                "type": "DDoS",
                "result": "Detected",
                "confidence": 95,
                "blocked": True,
                "payload": "N/A"
            })

    if current:
        entries.append(current)
    return entries


# Generate summary metrics
def generate_summary(data):
    return {
        "Total Requests": len(data),
        "XSS Detections": sum(1 for d in data if d.get("type", "").lower() == "xss" and "malicious" in d.get("result", "").lower()),
        "SQLi Detections": sum(1 for d in data if d.get("type", "").lower() == "sqli" and "malicious" in d.get("result", "").lower()),
        "DDoS Detections": sum(1 for d in data if d.get("type", "").lower() == "ddos"),
        "Blocked": sum(1 for d in data if d.get("blocked", False)),
    }


# Assign criticality level based on confidence
def assign_criticality(entry):
    conf = entry.get("confidence", 0)
    if conf >= 90:
        return "High"
    elif conf >= 70:
        return "Medium"
    else:
        return "Low"


# Real-world CVE/CVSS mappings
def get_cve_info(attack_type):
    if attack_type.lower() == "xss":
        return {
            "CVE": "CVE-2022-36067",
            "CVSS": "7.4",
            "Link": "https://nvd.nist.gov/vuln/detail/CVE-2022-36067"
        }
    elif attack_type.lower() == "sqli":
        return {
            "CVE": "CVE-2021-44228",
            "CVSS": "9.8",
            "Link": "https://nvd.nist.gov/vuln/detail/CVE-2021-44228"
        }
    elif attack_type.lower() == "ddos":
        return {
            "CVE": "CVE-2018-1000115",
            "CVSS": "7.5",
            "Link": "https://nvd.nist.gov/vuln/detail/CVE-2018-1000115"
        }
    else:
        return {"CVE": "-", "CVSS": "-", "Link": "-"}


# Export report as .docx
def export_report(summary, data):
    doc = Document()
    doc.add_heading("VULNBRACE Vulnerability Assessment Report", 0)
    doc.add_paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    doc.add_heading("Executive Summary", level=1)
    for key, value in summary.items():
        doc.add_paragraph(f"{key}: {value}")

    doc.add_heading("Detailed Detections", level=1)
    for entry in data:
        doc.add_paragraph(f"Timestamp: {entry.get('timestamp')}")
        doc.add_paragraph(f"Type: {entry.get('type')}")
        doc.add_paragraph(f"Result: {entry.get('result')}")
        doc.add_paragraph(f"Confidence: {entry.get('confidence', 'N/A')}")
        doc.add_paragraph(f"Criticality: {assign_criticality(entry)}")
        doc.add_paragraph(f"Payload: {entry.get('payload', 'N/A')}")
        cve_info = get_cve_info(entry.get("type", ""))
        doc.add_paragraph(f"CVE: {cve_info['CVE']} | CVSS: {cve_info['CVSS']}")
        doc.add_paragraph(f"Link: {cve_info['Link']}")
        doc.add_paragraph("-" * 50)

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer


# Streamlit UI
st.set_page_config(page_title="VULNBRACE Dashboard", layout="wide")
st.title("🔍 VULNBRACE Vulnerability Assessment Dashboard")
st.markdown(f"_Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_")

log_data = parse_logs()

if not log_data:
    st.warning("No logs found to generate report.")
else:
    for entry in log_data:
        entry["criticality"] = assign_criticality(entry)
        cve_info = get_cve_info(entry.get("type", ""))
        entry["CVE"] = cve_info["CVE"]
        entry["CVSS"] = cve_info["CVSS"]
        entry["Link"] = cve_info["Link"]

    summary = generate_summary(log_data)

    st.header("📊 Executive Summary")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Requests", summary["Total Requests"])
    col2.metric("XSS Detections", summary["XSS Detections"])
    col3.metric("SQLi Detections", summary["SQLi Detections"])
    col4.metric("DDoS Detections", summary["DDoS Detections"])
    col5.metric("Blocked Payloads", summary["Blocked"])

    st.subheader("📈 Attack Type Distribution")
    df = pd.DataFrame(log_data)
    type_counts = df['type'].value_counts()
    fig1, ax1 = plt.subplots()
    ax1.pie(type_counts, labels=type_counts.index, autopct='%1.1f%%', startangle=90)
    ax1.axis('equal')
    st.pyplot(fig1)

    st.subheader("🧾 Detailed Detection Logs")
    st.dataframe(df[["timestamp", "type", "result", "confidence", "criticality", "payload", "CVE", "CVSS", "Link"]])

    st.subheader("📄 Export Report")
    report_buffer = export_report(summary, log_data)
    st.download_button(
        label="📥 Download .docx Report",
        data=report_buffer,
        file_name="vulnbrace_report.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

    st.info("This report is generated live from the application logs.")
