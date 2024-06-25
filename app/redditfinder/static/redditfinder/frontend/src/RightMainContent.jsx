import React from 'react';
import mainContentSvg from './assets/main-content.svg';

const RightMainContent = () => {
    return (
        <div className='rightMain p-4'>
            <img src={mainContentSvg} alt='Main content illustration' className="w-full h-auto" />
        </div>
    );
};

export default RightMainContent;
