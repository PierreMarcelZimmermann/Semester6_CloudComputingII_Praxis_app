# flask 
from flask import Flask, request, jsonify
# file 
import os
from werkzeug.utils import secure_filename
# azure 
from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.core.credentials import AzureKeyCredential
# misc
import json
# db 
from sqlalchemy import create_engine
from urllib.parse import quote_plus

app = Flask(__name__)

# config locations
path_to_config = "aivision_config.json"
path_to_db_config = "db_config.json"

# Global variables for AI Vision and DB configurations
aivision_endpoint = None
aivision_key = None
engine = None
initialized = False  # Flag to ensure the configuration is loaded only once

from urllib.parse import quote_plus

@app.before_request
def configure_services():
    """
    This function is executed before each request. It loads the AI Vision and DB 
    configurations only once, using the `initialized` flag to prevent reloading 
    during subsequent requests.

    The function reads the configuration files for AI Vision and database 
    connection details, then initializes the global variables for these services.
    """
    global aivision_endpoint, aivision_key, engine, initialized

    if not initialized:
        # Load AI Vision configuration
        with open('aivision_config.json', 'r') as file:
            config = json.load(file)
        aivision_endpoint = config["AI_VISION_ENDPOINT"]
        aivision_key = config["AI_VISION_API_KEY"]
        
        # Load Database configuration
        with open('db_config.json', 'r') as file:
            config = json.load(file)
        hostname = config['server']
        database_name = config['database_name']
        username = config['username']
        password = config['password']
        
        # URL encode the password
        encoded_password = quote_plus(password)  # URL encode the password
        
        # Ensure that the connection string is properly formed
        connection_string = f"mysql+mysqlconnector://{username}:{encoded_password}@{hostname}/{database_name}"
        
        # Initialize the SQLAlchemy engine
        try:
            engine = create_engine(connection_string)
        except Exception as e:
            print(f"Error connecting to the database: {e}")
            raise

        initialized = True  # Mark as initialized to prevent reloading on subsequent requests


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
    if not aivision_endpoint or aivision_key == "Not Found" or not aivision_key or aivision_key == "Not Found":
        return jsonify({"error": "API credentials not set. Call /config first."}), 500

    # Azure Image Analysis Client erstellen
    client = ImageAnalysisClient(endpoint=aivision_endpoint, credential=AzureKeyCredential(aivision_key))

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
