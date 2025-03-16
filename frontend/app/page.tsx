"use client"; // Mark this file as a client component

import React, { useState, useEffect } from "react";
import "./page.css"; // Import the CSS file for styling

/**
 * This component handles the image upload process and displays the results.
 * It allows users to upload an image, sends it to the backend for analysis,
 * and then displays the caption and confidence of the image description.
 */
function App() {
    // State variables to store the uploaded file, caption, confidence, loading status, and backend public IP
    const [file, setFile] = useState<string | null>(null);
    const [caption, setCaption] = useState<string | null>(null);
    const [confidence, setConfidence] = useState<number | null>(null);
    const [loading, setLoading] = useState<boolean>(false);
    const [publicIp, setPublicIp] = useState<string | null>(null);

    /**
     * The useEffect hook loads the public IP address of the backend from the environment variable.
     * This is done when the component is first mounted.
     */
    useEffect(() => {
        // Load the public IP from the environment variable
        const publicIp = process.env.NEXT_PUBLIC_VM_PUBLIC_IP; // Load from environment variable
        if (publicIp) {
            setPublicIp(publicIp);
        } else {
            console.error("Public IP is not set in the environment variables.");
        }
    }, []);

    /**
     * Handles the file input change event when the user selects an image file.
     * It updates the preview of the image and initiates the image upload to the backend.
     *
     * @param e - The event triggered when a user selects a file.
     */
    function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
        if (e.target.files && e.target.files[0]) {
            // Set the file URL for preview and initiate upload
            setFile(URL.createObjectURL(e.target.files[0]));
            uploadImage(e.target.files[0]);
        }
    }

    /**
     * This function uploads the selected image to the backend server and receives the analyzed result.
     * It sends the image as a FormData object in a POST request.
     * Upon successful response, it updates the caption and confidence state with the backend's results.
     *
     * @param imageFile - The file object representing the image to be uploaded.
     */
    const uploadImage = async (imageFile: File) => {
        setLoading(true); // Set loading state to true while waiting for the server response

        const formData = new FormData();
        formData.append("image", imageFile); // Append the image to the form data

        try {
            // Check if the public IP address is available
            if (!publicIp) {
                throw new Error("Public IP is not available");
            }

            // Send a POST request to the backend to upload and analyze the image
            const response = await fetch(`http://${publicIp}:5000/upload_and_analyze`, {
                method: "POST",
                body: formData, // Attach the form data (image file)
            });

            if (!response.ok) {
                throw new Error("Image upload failed");
            }

            // Parse the JSON response containing the caption and confidence data
            const data = await response.json();
            setCaption(data.caption.text); // Set the caption text
            setConfidence(data.caption.confidence); // Set the confidence score
        } catch (error) {
            console.error("Error uploading image:", error);
        } finally {
            setLoading(false); // Set loading state to false once the request is complete
        }
    };

    return (
        <div className="App">
            <h2 className="heading">SkySight</h2>
            <div className="upload-container">
                {/* File input element for selecting an image */}
                <input
                    type="file"
                    id="file-input" // Unique ID for the input element
                    className="file-input"
                    onChange={handleChange} // Handle the change event when a file is selected
                    accept="image/*" // Accept only image files
                />
                {/* Label for the file input */}
                <label htmlFor="file-input" className="file-label">
                    <span className="label-text">Choose an image</span>
                </label>

                {/* Show loading text when the image is being uploaded */}
                {loading && <p>Loading...</p>}

                {/* Show the image preview once the file is selected and not loading */}
                {file && !loading && (
                    <div className="image-preview">
                        <img src={file} alt="Uploaded preview" />
                    </div>
                )}

                {/* Show the AI-generated caption and confidence once the image is analyzed */}
                {caption && !loading && (
                    <div>
                        <h3>AI sees:</h3>
                        <p>{caption}</p>
                        <p id="confidence">(Confidence: {(confidence ? (confidence * 100).toFixed(2) : 0)}%)</p>
                    </div>
                )}
            </div>
        </div>
    );
}

export default App;
