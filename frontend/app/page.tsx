"use client"; // Mark this file as a client component

import React, { useState, useEffect } from "react";
import "./page.css"; // Import the CSS file for styling

function App() {
    const [file, setFile] = useState<string | null>(null);
    const [caption, setCaption] = useState<string | null>(null);
    const [confidence, setConfidence] = useState<number | null>(null);
    const [loading, setLoading] = useState<boolean>(false);
    const [backendAddress, setBackendAddress] = useState<string | null>(null);

    // Load the react_config.json dynamically
    useEffect(() => {
        fetch("/react_config.json")  // Der Pfad zur JSON-Datei
            .then((response) => response.json())
            .then((data) => {
                setBackendAddress(data.backend_adress);  // Lädt die backend_adress von der JSON-Datei
            })
            .catch((error) => console.error("Error loading configuration:", error));
    }, []);

    function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
        if (e.target.files && e.target.files[0]) {
            setFile(URL.createObjectURL(e.target.files[0]));
            uploadImage(e.target.files[0]);
        }
    }

    const uploadImage = async (imageFile: File) => {
        setLoading(true);

        const formData = new FormData();
        formData.append("image", imageFile);

        try {
            if (!backendAddress) {
                throw new Error("Backend address is not available");
            }

            const response = await fetch(`http://${backendAddress}:5000/upload_and_analyze`, {
                method: "POST",
                body: formData,
            });

            if (!response.ok) {
                throw new Error("Image upload failed");
            }

            const data = await response.json();
            setCaption(data.caption.text);
            setConfidence(data.caption.confidence);
        } catch (error) {
            console.error("Error uploading image:", error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="App">
            <h2 className="heading">SkySight</h2>
            <div className="upload-container">
                {/* File input */}
                <input
                    type="file"
                    id="file-input" // Give the input a unique id
                    className="file-input"
                    onChange={handleChange}
                    accept="image/*"
                />
                {/* Label associated with the file input */}
                <label htmlFor="file-input" className="file-label">
                    <span className="label-text">Choose an image</span>
                </label>

                {loading && <p>Loading...</p>}

                {file && !loading && (
                    <div className="image-preview">
                        <img src={file} alt="Uploaded preview" />
                    </div>
                )}

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
