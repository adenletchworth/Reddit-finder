import React, { useRef } from 'react';
import useD3Animation from './useD3Animation';

function InfoPage() {
    const ref = useRef(null);

    useD3Animation(ref);

    return (
        <div className="container mx-auto p-4 mt-24">
            <h1 className="text-4xl font-bold text-primary-dark mb-8 text-center">About Thread Match</h1>
            <div className="relative flex flex-col items-center space-y-8" ref={ref}>
                <div className="info-rectangle relative w-full md:w-3/4 bg-primary-light text-primary-dark p-6 rounded-lg shadow-lg transform scale-0">
                    <h2 className="text-2xl font-bold mb-2">What is Thread Match?</h2>
                    <p>
                        Thread Match is a powerful tool that leverages semantic search technology to help you find similar threads on Reddit.
                        Whether you're trying to avoid duplicate content or seeking specific information, Thread Match helps you find exactly what you need.
                    </p>
                </div>
                <div className="info-rectangle relative w-full md:w-2/3 bg-secondary-light text-secondary-dark p-6 rounded-lg shadow-lg transform scale-0">
                    <h2 className="text-2xl font-bold mb-2">Why Use Thread Match?</h2>
                    <p>
                        Thread Match saves you time and effort by providing precise results based on the context and meaning of threads. It's an essential tool for researchers, moderators, and anyone looking to streamline their Reddit experience.
                    </p>
                </div>
                <div className="info-rectangle relative w-full md:w-3/4 bg-white text-gray-700 p-6 rounded-lg shadow-lg transform scale-0">
                    <h2 className="text-2xl font-bold mb-2">How It Works</h2>
                    <p>
                        Simply enter your search query, and Thread Match will analyze Reddit threads to find the most relevant matches. The app uses advanced algorithms to understand the context and meaning of each thread, delivering accurate results quickly.
                    </p>
                </div>
            </div>
        </div>
    );
}

export default InfoPage;
