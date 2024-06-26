import { useEffect } from 'react';
import * as d3 from 'd3';

const useSearchResultsAnimation = (ref, results) => {
    useEffect(() => {
        if (ref.current && results.length > 0) {
            const elements = d3.select(ref.current)
                .selectAll('.search-result-card')
                .style('opacity', '0')
                .style('transform', 'translateY(20px)');

            elements.each(function (d, i) {
                d3.select(this)
                    .transition()
                    .delay(i * 100) 
                    .duration(500)
                    .ease(d3.easeCubicOut)
                    .style('opacity', '1')
                    .style('transform', 'translateY(0)');
            });
        }
    }, [ref, results]);
};

export default useSearchResultsAnimation;
