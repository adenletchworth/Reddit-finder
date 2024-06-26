import React, { useRef } from 'react';
import useLandingPageAnimation from './useLandingPageAnimation';

const LeftMainContent = ({ title, subtitle, setCurrentPage }) => {
    const ref = useRef(null);

    useLandingPageAnimation(ref, '.left-main-content');

    return (
        <div className='leftMain p-4 flex flex-col h-full mt-32 ml-32' ref={ref}>
            <div className="left-main-content">
                <h1 className="text-6xl font-extrabold mb-6 text-primary-dark font-serif">{title}</h1>
                <p className="text-xl mb-4 text-secondary font-sans">{subtitle}</p>
            </div>
            <div className='left-main-content leftButtons mt-6 space-x-5'>
                <button 
                    className='btn bg-primary text-white'
                    onClick={() => setCurrentPage('search')}
                >
                    Search
                </button>
                <button 
                    className='btn bg-secondary text-white'
                    onClick={() => setCurrentPage('info')}
                >
                    Learn More
                </button>
            </div>
        </div>
    );
};

export default LeftMainContent;
