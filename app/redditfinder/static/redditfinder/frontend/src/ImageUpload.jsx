import React from 'react';

function ImageUpload({ onImageUpload }) {
    const handleFileChange = (event) => {
        const file = event.target.files[0];
        if (file) {
            onImageUpload(file);
        }
    };

    return (
        <div className="image-upload">
            <input 
                type="file" 
                accept="image/*" 
                onChange={handleFileChange} 
                className="file-input"
            />
        </div>
    );
}

export default ImageUpload;
