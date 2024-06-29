import React, { useState, useEffect, useRef } from 'react';
import SearchBar from './SearchBar';
import Card from './Card';
import useSearchResultsAnimation from './useSearchResultsAnimation';

function SearchPage({ header }) {
    const [searchQuery, setSearchQuery] = useState('');
    const [results, setResults] = useState([]);
    const [error, setError] = useState(null);
    const ref = useRef(null);

    const handleSearchChange = (event) => {
        setSearchQuery(event.target.value);
    };

    const handleFileUpload = (event) => {
        const file = event.target.files[0];
        if (file) {
            const formData = new FormData();
            formData.append('image', file);

            fetch('http://localhost:8000/search_image/', {
                method: 'POST',
                body: formData,
            })
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.json();
                })
                .then(data => {
                    setResults(data.metadata);
                    setError(null);
                })
                .catch(error => {
                    console.error('Error fetching search results:', error);
                    setError('Failed to fetch search results. Please try again.');
                });
        }
    };

    useEffect(() => {
        if (searchQuery) {
            fetch(`http://localhost:8000/search_text?query=${searchQuery}`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.json();
                })
                .then(data => {
                    setResults(data.metadata);
                    setError(null);
                })
                .catch(error => {
                    console.error('Error fetching search results:', error);
                    setError('Failed to fetch search results. Please try again.');
                });
        }
    }, [searchQuery]);

    useSearchResultsAnimation(ref, results);

    return (
        <div className="container mx-auto p-4 mt-24">
            <div className="mb-8 text-center">
                <h1 className="text-4xl font-bold text-primary-dark mb-4">{header}</h1>
                <SearchBar 
                    placeholder="Search..." 
                    onChange={handleSearchChange} 
                    onFileUpload={handleFileUpload}
                />
            </div>
            {error && <p className="text-accent">{error}</p>}
            <div className="grid grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-3" ref={ref}>
                {results.map((item, index) => (
                    <Card 
                        key={item.id} 
                        title={item.title} 
                        subreddit={item.subreddit}
                        author={item.author}
                        permalink={item.permalink}
                        className={`search-result-card order-${index}`}
                    />
                ))}
            </div>
        </div>
    );
}

export default SearchPage;
