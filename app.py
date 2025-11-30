from flask import Flask, jsonify, request, render_template
from dotenv import load_dotenv
import os
import uuid
import logging
from azure.storage.blob import BlobServiceClient
load_dotenv()  # reads .env into process env

app = Flask(__name__)

# Enable basic logging
logging.basicConfig(level=logging.INFO)

# Connect to Blob Storage
blob_service_client = BlobServiceClient.from_connection_string(
    os.environ.get('AZURE_STORAGE_CONNECTION_STRING')
)

CONTAINER_NAME = "ophthalmic-images"


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/v1/health')
def api():
    return jsonify({
        'status': 'ok'
    }), 200


@app.route('/api/v1/upload', methods=['POST'])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']

    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    # Prevent overwriting: create unique filename
    extension = file.filename.split('.')[-1]
    unique_filename = f"{uuid.uuid4()}.{extension}"

    try:
        container_client = blob_service_client.get_container_client(CONTAINER_NAME)
        container_client.upload_blob(unique_filename, file)

        url = f"{container_client.url}/{unique_filename}"

        logging.info(f"Uploaded file: {unique_filename}")

        return jsonify({"ok": True, "url": url}), 200

    except Exception as e:
        logging.error(f"Upload failed: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/v1/gallery', methods=['GET'])
def gallery():
    try:
        container_client = blob_service_client.get_container_client(CONTAINER_NAME)
        blobs = container_client.list_blobs()

        return jsonify({
            "ok": True,
            "gallery": [f"{container_client.url}/{blob.name}" for blob in blobs]
        }), 200

    except Exception as e:
        logging.error(f"Gallery error: {str(e)}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080, debug=True)
