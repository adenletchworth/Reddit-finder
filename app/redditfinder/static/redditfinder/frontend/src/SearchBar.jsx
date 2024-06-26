import React from 'react';

function SearchBar({ placeholder, onChange }) {
    return (
        <div className="search-bar">
            <input 
                type="text" 
                placeholder={placeholder} 
                onChange={onChange} 
                className="search-input"
            />
        </div>
    );
}

export default SearchBar;
