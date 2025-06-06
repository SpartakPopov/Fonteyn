from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# Configure these with your ERPNext instance info
ERP_URL = os.getenv("ERP_URL", "https://erpnext-fonteyn.duckdns.org")
API_KEY = os.getenv("ERP_API_KEY", "aae4c683a84e8f8")
API_SECRET = os.getenv("ERP_API_SECRET", "196347af676879c")

def erpnext_post(endpoint, data):
    url = f"{ERP_URL}/api/resource/{endpoint}"
    headers = {
        "Authorization": f"token {API_KEY}:{API_SECRET}",
        "Content-Type": "application/json"
    }
    return requests.post(url, json=data, headers=headers)

@app.route('/add_payment_entry', methods=['POST'])
def add_payment_entry():
    data = request.get_json()
    customer_name = data.get("party")
    # Step 1: Create Customer
    customer_data = {
        "customer_name": customer_name,
        "customer_type": "Individual",
        "customer_group": "Individual",
        "territory": "All Territories"
    }
    # Ignore error if customer already exists
    cust_resp = erpnext_post("Customer", customer_data)
    # Step 2: Create Payment Entry
    pay_resp = erpnext_post("Payment Entry", data)
    try:
        pay_json = pay_resp.json()
    except Exception:
        pay_json = pay_resp.text
    if pay_resp.status_code in [200, 201]:
        return jsonify({"success": True, "data": pay_json}), 201
    else:
        return jsonify({"success": False, "error": pay_json}), pay_resp.status_code

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
