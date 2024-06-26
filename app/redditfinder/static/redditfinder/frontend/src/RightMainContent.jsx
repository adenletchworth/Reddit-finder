import React, { useRef } from 'react';
import useLandingPageAnimation from './useLandingPageAnimation';
import mainContentSvg from './assets/main-content.svg';

const RightMainContent = () => {
    const ref = useRef(null);

    useLandingPageAnimation(ref, '.right-main-content');

    return (
        <div className='rightMain p-4' ref={ref}>
            <img src={mainContentSvg} alt='Main content illustration' className="right-main-content w-full h-auto opacity-0 transform translate-y-20" />
        </div>
    );
};

export default RightMainContent;
