from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import ImageAnalysisResult, Base  # Import the model

from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.core.credentials import AzureKeyCredential
from urllib.parse import quote_plus
from loguru import logger  # Import loguru

app = Flask(__name__)

# config locations
path_to_config = "aivision_config.json"
path_to_db_config = "db_config.json"

# Global variables for AI Vision and DB configurations
aivision_endpoint = None
aivision_key = None
engine = None
Session = None
initialized = False  # Flag to ensure the configuration is loaded only once

# Set up logging with loguru
logger.add("app.log", rotation="1 week", retention="10 days", compression="zip")

@app.before_request
def configure_services():
    """
    This function is executed before each request. It loads the AI Vision and DB 
    configurations only once, using the `initialized` flag to prevent reloading 
    during subsequent requests.
    """
    global aivision_endpoint, aivision_key, engine, Session, initialized

    if not initialized:
        try:
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
            logger.info(f"Connecting to database: {hostname}/{database_name}")
            engine = create_engine(connection_string)
            Session = sessionmaker(bind=engine)  # Create session factory
            Base.metadata.create_all(engine)  # Create the table if it doesn't exist
            logger.info("Database connection established successfully.")
        except Exception as e:
            logger.error(f"Error connecting to services: {e}")
            raise

        initialized = True  # Mark as initialized to prevent reloading on subsequent requests

@app.route("/upload_and_analyze", methods=["POST"])
def upload_and_analyze():
    if not aivision_endpoint or not aivision_key:
        logger.error("API credentials not set. Call /config first.")
        return jsonify({"error": "API credentials not set. Call /config first."}), 500

    # Azure Image Analysis Client erstellen
    client = ImageAnalysisClient(endpoint=aivision_endpoint, credential=AzureKeyCredential(aivision_key))

    if "image" not in request.files:
        logger.error("No image file provided")
        return jsonify({"error": "No image file provided"}), 400

    image = request.files["image"]
    
    if image.filename == "":
        logger.error("No selected file")
        return jsonify({"error": "No selected file"}), 400

    filename = secure_filename(image.filename)
    
    # Datei als Bytes lesen
    image_bytes = image.read()

    # Bildanalyse durchführen
    try:
        logger.info(f"Starting image analysis for file: {filename}")
        result = client.analyze(
            image_data=image_bytes,
            visual_features=[VisualFeatures.CAPTION, VisualFeatures.READ],
            gender_neutral_caption=True
        )
        logger.info(f"Image analysis completed for file: {filename}")
    except Exception as e:
        logger.error(f"Error analyzing image: {e}")
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

    # Save to the database
    try:
        session = Session()  # Create a new session
        new_result = ImageAnalysisResult(
            caption_text=response_data["caption"]["text"],
            caption_confidence=response_data["caption"]["confidence"],
            read_text=json.dumps(response_data["read_text"])  # Convert read text to a JSON string
        )
        session.add(new_result)  # Add to session
        session.commit()  # Commit transaction
        session.close()  # Close the session
        logger.info("Image analysis result saved to the database.")
    except Exception as e:
        logger.error(f"Error saving to database: {str(e)}")
        return jsonify({"error": f"Error saving to database: {str(e)}"}), 500

    return jsonify(response_data)


if __name__ == "__main__":
    logger.info("Starting Flask app...")
    app.run(debug=True)
    logger.info("Flask app stopped.")
