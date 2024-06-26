import { useEffect } from 'react';
import * as d3 from 'd3';

const useD3Animation = (ref) => {
    useEffect(() => {
        if (ref.current) {
            const rectangles = d3.select(ref.current)
                .selectAll('.info-rectangle')
                .style('transform', 'scale(0) rotate(0deg)')
                .style('opacity', '0');

            rectangles.each(function (d, i) {
                d3.select(this)
                    .transition()
                    .delay(i * 250) 
                    .duration(500)
                    .ease(d3.easeBounceOut)
                    .style('transform', 'scale(1) rotate(5deg)')
                    .style('opacity', '1')
                    .transition()
                    .duration(500)
                    .style('transform', 'rotate(0deg)')
                    .on('end', function () {
                        d3.select(this)
                            .transition()
                            .duration(1000)
                            .style('border-color', '#ff6b6b')
                            .style('box-shadow', '0 0 20px rgba(255, 107, 107, 0.5)')
                            .transition()
                            .duration(1000)
                            .style('border-color', '')
                            .style('box-shadow', '');
                    });
            });
        }
    }, [ref]);
};

export default useD3Animation;
