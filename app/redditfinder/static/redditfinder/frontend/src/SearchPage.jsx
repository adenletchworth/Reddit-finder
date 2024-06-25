import React, { useState, useEffect } from 'react';
import SearchBar from './SearchBar';
import Card from './Card';

function SearchPage() {
    const [searchQuery, setSearchQuery] = useState('');
    const [results, setResults] = useState([]);
    const [error, setError] = useState(null);

    const handleSearchChange = (event) => {
        setSearchQuery(event.target.value);
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

    return (
        <div className="container mx-auto p-4 mt-24">
            <h1 className="text-2xl font-bold mb-4">Search Page</h1>
            <SearchBar 
                placeholder="Search..." 
                onChange={handleSearchChange} 
            />
            {error && <p className="text-red-500">{error}</p>}
            <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
                {results.map((item) => (
                    <Card 
                        key={item.id} 
                        title={item.title} 
                        subreddit={item.subreddit}
                        author={item.author}
                        permalink={item.permalink}
                    />
                ))}
            </div>
        </div>
    );
}

export default SearchPage;
