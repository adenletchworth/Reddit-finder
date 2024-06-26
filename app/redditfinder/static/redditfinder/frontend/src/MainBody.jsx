import React from 'react';
import LeftMainContent from './LeftMainContent';
import RightMainContent from './RightMainContent'; 

const MainBody = ({ setCurrentPage }) => {
    return (
        <div className="main-body grid grid-cols-1 md:grid-cols-2 gap-4 p-4 mt-24">
            <LeftMainContent 
                title="Thread Match!" 
                subtitle="Thread Match utilizes cutting-edge semantic search technology to identify similar posts on Reddit. Whether you're aiming to avoid duplicate content or looking for specific information, Thread Match efficiently finds exactly what you need by analyzing the meaning and context of each thread."
                setCurrentPage={setCurrentPage}
            />
            <RightMainContent />
        </div>
    );
};

export default MainBody;
