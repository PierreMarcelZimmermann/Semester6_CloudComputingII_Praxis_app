import hashlib
import os
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import ImageAnalysisResult, Base  # Import the model

from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.core.credentials import AzureKeyCredential
from urllib.parse import quote_plus
from loguru import logger  # Import loguru
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app)

# Global variables for AI Vision and DB configurations
aivision_endpoint = None
aivision_key = None
engine = None
Session = None
initialized = False  # Flag to ensure the configuration is loaded only once

# Set up logging with loguru
logger.add("app.log", rotation="1 week", retention="10 days", compression="zip")

def calculate_image_hash(image_bytes):
    """
    Calculates the SHA-256 hash of an image to provide a unique identifier.
    
    Args:
        image_bytes (bytes): The image content in bytes.
        
    Returns:
        str: The SHA-256 hash of the image.
    """
    return hashlib.sha256(image_bytes).hexdigest()

@app.before_request
def configure_services():
    """
    This function is executed before each request. It loads the AI Vision and DB configurations 
    only once, using the `initialized` flag to prevent reloading during subsequent requests.
    """
    global aivision_endpoint, aivision_key, engine, Session, initialized

    if not initialized:
        try:
            # Load AI Vision configuration from environment variables
            aivision_endpoint = os.getenv("AI_VISIONS_ENDPOINT")
            aivision_key = os.getenv("AI_VISION_API_KEY")
            
            # Load Database configuration from environment variables
            hostname = os.getenv('DB_SERVER')
            database_name = os.getenv('DB')
            username = os.getenv('DB_ADMIN')
            password = os.getenv('DB_PASSWORD')
            
            # URL encode the password
            encoded_password = quote_plus(password.encode())  # URL encode the password
            
            # Form the connection string
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
    """
    Endpoint to upload an image and analyze it using Azure's AI Vision service. If the image has been 
    analyzed before, the result is fetched from the database.

    Returns:
        Response: JSON object containing the analysis results.
    """
    if not aivision_endpoint or not aivision_key:
        logger.error("API credentials not set. Call /config first.")
        return jsonify({"error": "API credentials not set. Call /config first."}), 500

    # Create Azure Image Analysis Client
    client = ImageAnalysisClient(endpoint=aivision_endpoint, credential=AzureKeyCredential(aivision_key))

    if "image" not in request.files:
        logger.error("No image file provided")
        return jsonify({"error": "No image file provided"}), 400

    image = request.files["image"]
    
    if image.filename == "":
        logger.error("No selected file")
        return jsonify({"error": "No selected file"}), 400

    filename = secure_filename(image.filename)
    
    # Read image as bytes
    image_bytes = image.read()

    # Calculate the hash of the image
    image_hash = calculate_image_hash(image_bytes)

    # Check if the image has already been analyzed
    try:
        session = Session()  # Create a new session
        existing_result = session.query(ImageAnalysisResult).filter_by(image_hash=image_hash).first()
        session.close()

        if existing_result:
            # If the image has already been analyzed, return the result from the DB
            logger.info(f"Image already analyzed, returning results for {filename}")
            response_data = {
                "caption": {
                    "text": existing_result.caption_text,
                    "confidence": existing_result.caption_confidence
                }
            }
            return jsonify(response_data)
    except Exception as e:
        logger.error(f"Error checking for existing entry in the database: {e}")
        return jsonify({"error": "Error checking the database"}), 500

    # Perform image analysis if not already analyzed
    try:
        logger.info(f"Starting image analysis for file: {filename}")
        result = client.analyze(
            image_data=image_bytes,
            visual_features=[VisualFeatures.CAPTION],
            gender_neutral_caption=True
        )
        logger.info(f"Image analysis completed for file: {filename}")
    except Exception as e:
        logger.error(f"Error analyzing image: {e}")
        return jsonify({"error": str(e)}), 500

    response_data = {
        "caption": {
            "text": result.caption.text if result.caption else None,
            "confidence": float(result.caption.confidence) if result.caption else None
        }
    }

    # Save the result in the database
    try:
        session = Session()
        new_result = ImageAnalysisResult(
            image_hash=image_hash,  # Save the image hash
            caption_text=response_data["caption"]["text"],
            caption_confidence=response_data["caption"]["confidence"]
        )
        session.add(new_result)
        session.commit()
        session.close()
        logger.info("Image analysis result saved to the database.")
    except Exception as e:
        logger.error(f"Error saving to database: {str(e)}")
        return jsonify({"error": f"Error saving to database: {str(e)}"}), 500

    return jsonify(response_data)

@app.route("/get_all_entries", methods=["GET"])
def get_all_entries():
    """
    Endpoint to retrieve all image analysis results from the database.

    Returns:
        Response: JSON object containing all image analysis entries.
    """
    try:
        session = Session()  # Create a new session
        results = session.query(ImageAnalysisResult).all()  # Retrieve all results from the database
        session.close()  # Close the session

        # Convert the results into a list of dictionaries
        entries = []
        for result in results:
            entries.append({
                "id": result.id,
                "caption_text": result.caption_text,
                "caption_confidence": result.caption_confidence,
            })
        
        return jsonify(entries)
    except Exception as e:
        logger.error(f"Error fetching entries from database: {e}")
        return jsonify({"error": f"Error fetching entries from database: {e}"}), 500

if __name__ == "__main__":
    logger.info("Starting Flask app...")
    app.run(debug=True)
    logger.info("Flask app stopped.")
