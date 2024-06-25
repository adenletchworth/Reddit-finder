import React from 'react';

function Card({ title, subreddit, author, permalink }) {
    return (
        <div className="p-6 bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow duration-300">
            <h2 className="text-2xl font-bold mb-2 text-gray-800">{title}</h2>
            <div className="text-sm text-gray-500">
                <p><strong>Subreddit:</strong> {subreddit}</p>
                <p><strong>Author:</strong> {author}</p>
                <p>
                    <strong>Link:</strong> 
                    <a 
                        href={`https://reddit.com${permalink}`} 
                        target="_blank" 
                        rel="noopener noreferrer" 
                        className="text-blue-500 hover:underline"
                    >
                        {` https://reddit.com${permalink}`}
                    </a>
                </p>
            </div>
        </div>
    );
}

export default Card;
