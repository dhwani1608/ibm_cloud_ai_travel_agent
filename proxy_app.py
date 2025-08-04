import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app) # Handles Cross-Origin requests from the frontend

# We will set these as local environment variables
WATSONX_API_URL = os.getenv("kBzQCLC3EhQvqfetyDozVjHtG-SB0rb2OD5WzKOUgHlx")
IBM_API_KEY = os.getenv("iXtyVxhGvEQJzWVdMSvxTuKlGGZ87jU5v1kZxJqkPrTy")
IAM_TOKEN_URL = "https://iam.cloud.ibm.com/identity/token"

def get_iam_token():
    """Exchanges the API Key for a temporary IAM token."""
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {"apikey": IBM_API_KEY, "grant_type": "urn:ibm:params:oauth:grant-type:apikey"}
    response = requests.post(IAM_TOKEN_URL, headers=headers, data=data)
    response.raise_for_status()
    return response.json()["access_token"]

@app.route('/api/get-plan', methods=['POST'])
def proxy_request():
    """Receives request from frontend and calls the watsonx API."""
    if not WATSONX_API_URL or not IBM_API_KEY:
        return jsonify({"error": "Server not configured. Please set environment variables."}), 500

    user_query = request.json.get('query')
    if not user_query:
        return jsonify({"error": "No query provided."}), 400

    try:
        iam_token = get_iam_token()

        payload = {
            "input": f"""You are an expert AI Travel Planner... (Use your full text-based prompt here) --- {user_query} ---""",
            "parameters": {"decoding_method": "greedy", "max_new_tokens": 1500},
            "project_id": os.getenv("10616e78-dbaf-4a7c-aa2f-1b99fd30c175") # Add project_id here
        }

        headers = {'Authorization': f'Bearer {iam_token}', 'Content-Type': 'application/json'}

        response = requests.post(WATSONX_API_URL, headers=headers, json=payload)
        response.raise_for_status()

        result_json = response.json()
        generated_text = result_json.get('results', [{}])[0].get('generated_text', 'Sorry, could not generate a plan.')

        return generated_text, 200

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("Starting local server on http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000)