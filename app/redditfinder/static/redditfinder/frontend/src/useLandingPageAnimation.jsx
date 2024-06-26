import { useEffect } from 'react';
import * as d3 from 'd3';

const useLandingPageAnimation = (ref, className) => {
    useEffect(() => {
        if (ref.current) {
            const elements = d3.select(ref.current)
                .selectAll(className)
                .style('opacity', '0')
                .style('transform', 'translateY(20px)');

            elements.each(function (d, i) {
                d3.select(this)
                    .transition()
                    .delay(i * 100) 
                    .duration(250)
                    .ease(d3.easeCubicOut)
                    .style('opacity', '1')
                    .style('transform', 'translateY(0)');
            });
        }
    }, [ref, className]);
};

export default useLandingPageAnimation;
