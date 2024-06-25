import React from 'react';

function SearchBar({ placeholder, onChange }) {
    return (
        <div className="mb-4">
            <input 
                type="text" 
                placeholder={placeholder} 
                onChange={onChange} 
                className="w-full px-4 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
        </div>
    );
}

export default SearchBar;
