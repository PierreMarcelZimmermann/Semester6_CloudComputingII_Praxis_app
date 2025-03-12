from flask import Flask, request, jsonify
import os
from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.core.credentials import AzureKeyCredential
from werkzeug.utils import secure_filename
import json

app = Flask(__name__)

path_to_config = "aivision_config.json"

@app.route("/config", methods=["GET"])
def config():
    # Konfigurationsdatei auslesen und Umgebungsvariablen setzen
    with open(path_to_config, "r") as file:
        data = json.load(file)

    os.environ["VISION_KEY"] = data.get("AI_VISION_API_KEY", "Not Found")
    os.environ["VISION_ENDPOINT"] = data.get("AI_VISION_ENDPOINT", "Not Found")

    return jsonify(data)

@app.route("/upload_and_analyze", methods=["POST"])
def upload_and_analyze():
    # Umgebungsvariablen zur Laufzeit abrufen
    endpoint = os.environ.get("VISION_ENDPOINT")
    key = os.environ.get("VISION_KEY")

    if not endpoint or endpoint == "Not Found" or not key or key == "Not Found":
        return jsonify({"error": "API credentials not set. Call /config first."}), 500

    # Azure Image Analysis Client erstellen
    client = ImageAnalysisClient(endpoint=endpoint, credential=AzureKeyCredential(key))

    if "image" not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    image = request.files["image"]
    
    if image.filename == "":
        return jsonify({"error": "No selected file"}), 400

    filename = secure_filename(image.filename)
    
    # Datei als Bytes lesen
    image_bytes = image.read()

    # Bildanalyse durchführen
    try:
        result = client.analyze(
            image_data=image_bytes,
            visual_features=[VisualFeatures.CAPTION, VisualFeatures.READ],
            gender_neutral_caption=True
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # Ergebnisse verarbeiten
    response_data = {
        "caption": {
            "text": result.caption.text if result.caption else None,
            "confidence": result.caption.confidence if result.caption else None,
        },
        "read_text": []
    }

    if result.read:
        for block in result.read.blocks:
            for line in block.lines:
                response_data["read_text"].append({
                    "text": line.text,
                    "bounding_box": line.bounding_polygon
                })

    return jsonify(response_data)

if __name__ == "__main__":
    app.run(debug=True)
