import React from 'react';

function Card({ title, subreddit, author, permalink, className }) {
    return (
        <a 
            href={`https://reddit.com${permalink}`} 
            target="_blank" 
            rel="noopener noreferrer" 
            className={`card ${className}`}
        >
            <h2 className="card-title">{title}</h2>
            <div className="card-subtext">
                <p><strong>Subreddit:</strong> {subreddit}</p>
                <p><strong>Author:</strong> {author}</p>
            </div>
        </a>
    );
}

export default Card;
