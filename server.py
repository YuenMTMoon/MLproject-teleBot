from flask import Flask, request, jsonify, render_template
import json
import redis
import uuid
from datetime import datetime
import base64
import requests

app = Flask(__name__)
r = redis.Redis()  # Create Redis connection

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/process", methods=["POST"])
def process_request():
    try:
        if "url" in request.form:
            url = request.form["url"]
            # Validate URL
            if not is_valid_url(url):
                return jsonify({"error": "Invalid URL format"}), 400
            message = {
                "timestamp": str(datetime.now()),
                "url": url
            }
            r.lpush("image", json.dumps(message))
        elif "image" in request.files:
            image_file = request.files["image"]
            image_data = image_file.read()
            encoded_image = base64.b64encode(image_data).decode("utf-8")
            message = {
                "timestamp": str(datetime.now()),
                "url": "uploaded_image",
                "image": encoded_image
            }
            r.lpush("image", json.dumps(message))
        else:
            return jsonify({"error": "URL or image file not provided"}), 400

        task_id = str(uuid.uuid4())
        return jsonify({"task_id": task_id}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/result/<string:task_id>")
def get_result(task_id):
    try:
        result = r.get(task_id)
        if result is None:
            return jsonify({"error": "Result not found for task ID"}), 404
        else:
            return jsonify(json.loads(result)), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def is_valid_url(url):
    try:
        response = requests.head(url)
        return response.status_code == 200
    except:
        return False

if __name__ == "__main__":
    app.run(host="localhost", port=5000)
