from flask import Flask, request
import pickle
import os

app = Flask(__name__)
PICKLE_FILE = "webhook_data.pkl"


def safe_str(item):
    # If the item is bytes, try to decode it, else convert to string.
    if isinstance(item, bytes):
        try:
            return item.decode('utf-8')
        except Exception:
            return str(item)
    return str(item)


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.data  # Get raw text payload from POST request
    # Load existing data if file exists, else start with an empty list
    if os.path.exists(PICKLE_FILE):
        with open(PICKLE_FILE, "rb") as f:
            existing_data = pickle.load(f)
        if not isinstance(existing_data, list):
            existing_data = [existing_data]
    else:
        existing_data = []

    # Decode the incoming data and append it
    decoded_data = data.decode('utf-8')
    existing_data.append(decoded_data)

    # Save back to the file
    with open(PICKLE_FILE, "wb") as f:
        pickle.dump(existing_data, f)

    return "Data saved successfully", 200


@app.route("/webhook", methods=["GET"])
def get_webhook_data():
    if not os.path.exists(PICKLE_FILE):
        return "No data available", 404
    with open(PICKLE_FILE, "rb") as f:
        data = pickle.load(f)
    # Convert every entry to a safe string before joining
    return "\n".join(safe_str(item) for item in data), 200


@app.route("/webhook", methods=["DELETE"])
def delete_webhook_text():
    if not os.path.exists(PICKLE_FILE):
        return "No data available", 404

    # Get the text to delete from request body (as a decoded string)
    delete_text = request.data.decode('utf-8')

    # Load existing data
    with open(PICKLE_FILE, "rb") as f:
        data = pickle.load(f)

    # Ensure data is a list
    if not isinstance(data, list):
        data = [data]


    # If no delete text provided (empty or only whitespace), clear alldata
    if not delete_text.strip():
        new_data = []
        message = "All data cleared"
    else:
        # Otherwise, filter out entries that match the delete_text exactly
        new_data = [entry for entry in data if safe_str(entry) !=
                    delete_text]
        if len(new_data) == len(data):
            return "Text not found", 404
        message = f"Deleted occurrences of '{delete_text}'"

    # Save the updated data back
    with open(PICKLE_FILE, "wb") as f:
        pickle.dump(new_data, f)

    return message, 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
