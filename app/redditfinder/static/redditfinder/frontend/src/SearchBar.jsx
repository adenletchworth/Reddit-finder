import React from 'react';
import { Icon } from '@iconify/react';
import baselineCloudUpload from '@iconify-icons/ic/baseline-cloud-upload';

function SearchBar({ placeholder, onChange, onFileUpload }) {
    return (
        <div className="search-bar flex items-center mb-4">
            <label htmlFor="file-upload" className="cursor-pointer text-gray-500 mr-2">
                <Icon icon={baselineCloudUpload} width="24" height="24" />
            </label>
            <input 
                type="file" 
                id="file-upload" 
                className="hidden" 
                onChange={onFileUpload} 
            />
            <input 
                type="text" 
                placeholder={placeholder} 
                onChange={onChange} 
                className="search-input w-full px-6 py-3 border border-primary-light rounded-full shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-light focus:border-primary-light"
            />
        </div>
    );
}

export default SearchBar;
