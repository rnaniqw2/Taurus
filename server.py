from flask import Flask, request, render_template_string
import pickle
import os
import requests
import base64

app = Flask(__name__)
PICKLE_FILE = "webhook_data.pkl"

def safe_str(item):
    if isinstance(item, bytes):
        try:
            return item.decode('utf-8')
        except Exception:
            return str(item)
    return str(item)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.data
    if os.path.exists(PICKLE_FILE):
        with open(PICKLE_FILE, "rb") as f:
            existing_data = pickle.load(f)
        if not isinstance(existing_data, list):
            existing_data = [existing_data]
    else:
        existing_data = []

    decoded_data = data.decode('utf-8')
    existing_data.append(decoded_data)
    
    with open(PICKLE_FILE, "wb") as f:
        pickle.dump(existing_data, f)
    
    return "Data saved successfully", 200

@app.route("/webhook", methods=["GET"])
def get_webhook_data():
    if not os.path.exists(PICKLE_FILE):
        return "No data available", 404
    with open(PICKLE_FILE, "rb") as f:
        data = pickle.load(f)
    return "\n".join(safe_str(item) for item in data), 200

@app.route("/webhook", methods=["DELETE"])
def delete_webhook_text():
    if not os.path.exists(PICKLE_FILE):
        return "No data available", 404

    delete_text = request.data.decode('utf-8')
    
    with open(PICKLE_FILE, "rb") as f:
        data = pickle.load(f)
    
    if not isinstance(data, list):
        data = [data]

    if not delete_text.strip():
        new_data = []
        message = "All data cleared"
    else:
        new_data = [entry for entry in data if safe_str(entry) != delete_text]
        if len(new_data) == len(data):
            return "Text not found", 404
        message = f"Deleted occurrences of '{delete_text}'"

    with open(PICKLE_FILE, "wb") as f:
        pickle.dump(new_data, f)
    
    return message, 200

@app.route("/webhook", methods=["PUT"])
def generate_image():
    """
    Expects a JSON payload with:
    {
      "account_id": "EXAMPLEID",
      "model": "EXAMPLEMODEL",
      "api_key": "EXAMPLEKEY",
      "prompt": "EXAMPLEPROMPT"
    }
    """
    data = request.get_json(force=True)
    account_id = data.get("account_id")
    model = data.get("model")
    api_key = data.get("api_key")
    prompt = data.get("prompt")

    if not all([account_id, model, api_key, prompt]):
        return "Missing required fields", 400

    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {"prompt": prompt}

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
    except Exception as e:
        return f"Error generating image: {str(e)}", 500

    # Encode the response content (the image) in base64 and return it
    b64_img = base64.b64encode(response.content).decode('utf-8')
    return b64_img, 200

# Simple web interface that runs on old phones, minimalist & dark mode
@app.route("/")
def index():
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Webhook Interface</title>
      <style>
        body {
          background-color: #121212;
          color: #e0e0e0;
          font-family: Arial, sans-serif;
          margin: 0;
          padding: 20px;
        }
        h1 { text-align: center; }
        .container {
          max-width: 480px;
          margin: auto;
        }
        label { display: block; margin-top: 15px; }
        input[type="text"], textarea {
          width: 100%;
          padding: 10px;
          border: none;
          border-radius: 4px;
          margin-top: 5px;
          background-color: #1e1e1e;
          color: #e0e0e0;
        }
        button {
          margin-top: 10px;
          padding: 10px;
          width: 100%;
          border: none;
          border-radius: 4px;
          background-color: #6200ea;
          color: white;
          font-size: 16px;
        }
        button:hover { background-color: #3700b3; }
        .result { margin-top: 20px; white-space: pre-wrap; background-color: #1e1e1e; padding: 10px; border-radius: 4px; }
      </style>
    </head>
    <body>
      <div class="container">
        <h1>Webhook Interface</h1>
        <form id="postForm">
          <label for="postData">Enter text to add:</label>
          <input type="text" id="postData" required>
          <button type="submit">Submit (POST)</button>
        </form>
        <form id="deleteForm">
          <label for="deleteData">Enter text to delete (leave blank to clear all):</label>
          <input type="text" id="deleteData">
          <button type="submit">Delete (DELETE)</button>
        </form>
        <button id="refreshButton">Refresh Data (GET)</button>
        <div class="result" id="resultArea">Data will appear here...</div>
      </div>
      <script>
        const resultArea = document.getElementById('resultArea');
        
        document.getElementById('postForm').addEventListener('submit', async (e) => {
          e.preventDefault();
          const text = document.getElementById('postData').value;
          const response = await fetch('/webhook', { method: 'POST', body: text });
          const resText = await response.text();
          resultArea.textContent = resText;
          document.getElementById('postData').value = '';
        });
        
        document.getElementById('deleteForm').addEventListener('submit', async (e) => {
          e.preventDefault();
          const text = document.getElementById('deleteData').value;
          const response = await fetch('/webhook', { method: 'DELETE', body: text });
          const resText = await response.text();
          resultArea.textContent = resText;
          document.getElementById('deleteData').value = '';
        });
        
        document.getElementById('refreshButton').addEventListener('click', async () => {
          const response = await fetch('/webhook');
          const resText = await response.text();
          resultArea.textContent = resText;
        });
      </script>
    </body>
    </html>
    """
    return render_template_string(html)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

