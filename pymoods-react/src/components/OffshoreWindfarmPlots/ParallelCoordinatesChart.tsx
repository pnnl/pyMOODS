import React, { useEffect, useRef, useState } from 'react';
import { Box } from '@mui/material';
import * as d3 from 'd3';

// Define types
interface RankDict {
  [key: string]: Record<string, number>;
}

interface ParallelCoordinatesChartProps {
  ranks: RankDict;
}

const ParallelCoordinatesChart: React.FC<ParallelCoordinatesChartProps> = ({ ranks }) => {
  const ref = useRef<SVGSVGElement | null>(null);
  const [sliderValue, setSliderValue] = useState<number>(0.5);

  // Flatten rank data and compute rankings
  const processData = () => {
    if (!ranks || Object.keys(ranks).length === 0) return { rankedData: [], numericColumns: [] };

    const flatData = Object.entries(ranks).map(([key, values]) => {
      const [config, site] = key.split(',');
      return {
        config,
        site,
        ...values,
      };
    });

    const numericColumns = Object.keys(flatData[0]).filter(
      key => typeof flatData[0][key] === 'number'
    );

    const rankedData = [...flatData];
    numericColumns.forEach(col => {
      const sorted = [...flatData].sort((a, b) => a[col] - b[col]);
      sorted.forEach((row, i) => {
        const index = rankedData.findIndex(r => r.config === row.config && r.site === row.site);
        if (index > -1) {
          rankedData[index][`${col}_rank`] = i + 1;
        }
      });
    });

    return { rankedData, numericColumns };
  };

  const draw = () => {
    const svg = d3.select(ref.current);
    svg.selectAll('*').remove(); // Clear previous content

    const boundingRect = svg.node()?.getBoundingClientRect();
    const containerWidth = boundingRect ? boundingRect.width : 900;

    const margin = { top: 20, right: 0, bottom: 30, left: 0 };
    const width = containerWidth - margin.left - margin.right;
    const height = 250 - margin.top - margin.bottom;

    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    const { rankedData, numericColumns } = processData();
    if (!rankedData.length) return;

    const rankColumns = numericColumns.map(c => `${c}_rank`);

    // Color scale by configuration
    const configs = [...new Set(rankedData.map(d => d.config))];
    const colorScale = d3.scaleOrdinal(d3.schemeCategory10).domain(configs);
    const colorMap = Object.fromEntries(configs.map(config => [config, colorScale(config)]));

    // Create scales
    const yScales: Record<string, d3.ScaleLinear<number, number>> = {};
    const xScale = d3.scalePoint()
      .domain(rankColumns)
      .range([0, width])
      .padding(0.35);

    rankColumns.forEach(col => {
      const extent = d3.extent(rankedData, d => d[col]);
      yScales[col] = d3.scaleLinear()
        .domain(extent as [number, number])
        .range([height, 0]);
    });

    // Tooltip
    const tooltip = d3.select('body').append('div')
      .attr('class', 'tooltip')
      .style('position', 'absolute')
      .style('text-align', 'center')
      .style('width', 'auto')
      .style('height', 'auto')
      .style('padding', '6px 12px')
      .style('font-size', '14px')
      .style('background', 'white')
      .style('border', '1px solid #ccc')
      .style('border-radius', '4px')
      .style('opacity', 0);

    // Draw lines
    g.selectAll('.line')
      .data(rankedData)
      .enter()
      .append('path')
      .attr('class', d => `line ${d.config.replace(/\s+/g, '')}`)
      .attr('fill', 'none')
      .attr('stroke', d => colorMap[d.config] || '#9467bd')
      .attr('stroke-width', 2)
      .attr('d', d =>
        d3.line()
          .x(p => xScale(p[0]))
          .y(p => yScales[p[0]](d[p[0]]))
          (rankColumns.map(dim => [dim, d[dim]]))
      )
      .on('mouseover', function(event, d) {
        d3.select(this).attr('stroke-width', 4);
        tooltip.transition().duration(200).style('opacity', .9);
        tooltip.html(`${d.config} - ${d.site}`)
                 .style('left', (event.pageX + 10) + 'px')
                 .style('top', (event.pageY - 28) + 'px');
      })
      .on('mouseout', function() {
        d3.select(this).attr('stroke-width', 2);
        tooltip.transition().duration(500).style('opacity', 0);
      });

    // Y-axis on first dimension
    const firstDim = rankColumns[0];
    const yAxisGroup = g.append('g')
      .attr('transform', `translate(${xScale(firstDim)},0)`)
      .call(d3.axisLeft(yScales[firstDim]).ticks(5));
    yAxisGroup.selectAll('text').remove();

    // Axis guide lines
    rankColumns.forEach((col) => {
      g.append('line')
        .attr('x1', xScale(col))
        .attr('x2', xScale(col))
        .attr('y1', 0)
        .attr('y2', height)
        .attr('stroke', '#eee');
    });

    // Text wrapping utility
    const wrapText = (text: d3.Selection<SVGTextElement, any, any, any>, width: number) => {
      text.each(function () {
        const text = d3.select(this);
        let words = text.text().split(/\s+/).reverse();
        let word;
        let line: string[] = [];
        let lineNumber = 0;
        const lineHeight = 1.2;
        const y = text.attr('y');
        const x = text.attr('x') || 0;
        text.text(null);
        let tspan = text.append('tspan')
          .attr('x', x)
          .attr('y', y)
          .attr('dy', '0em');
        while ((word = words.pop())) {
          line.push(word);
          tspan.text(line.join(' '));
          if (tspan.node()?.getComputedTextLength()! > width) {
            line.pop();
            tspan.text(line.join(' '));
            line = [word];
            lineNumber++;
            tspan = text.append('tspan')
              .attr('x', x)
              .attr('y', y)
              .attr('dy', `${lineNumber * lineHeight}em`)
              .text(word);
          }
        }
      });
    };

    // Add metric names at the bottom
    g.selectAll('.metric-label')
      .data(rankColumns)
      .enter()
      .append('text')
      .attr('class', 'metric-label')
      .attr('x', d => xScale(d))
      .attr('y', height + 20)
      .attr('text-anchor', 'middle')
      .style('font-size', '14px')
      .text((d, i) => numericColumns[i])
      .call(wrapText, 60);
  };

  // Redraw chart on resize
  useEffect(() => {
    draw();

    const resizeObserver = new ResizeObserver(() => {
      draw();
    });

    if (ref.current) {
      resizeObserver.observe(ref.current);
    }

    return () => {
      if (ref.current) {
        resizeObserver.unobserve(ref.current);
      }
    };
  }, [ranks]);

  // Slider handler
  const handleSliderChange = (value: number) => {
    setSliderValue(value);
    console.log("Slider value:", value);
    // You can pass this to backend or update the chart accordingly
  };

  // Styles inside the component
  const styles = {
    container: {
      display: 'flex',
      alignItems: 'center',
      width: '100%',
      minHeight: '300px',
      position: 'relative' as const,
    },
    chart: {
      flexGrow: 1,
      height: 'auto',
      minHeight: '300px',
    },
    sliderContainer: {
      display: 'flex',
      flexDirection: 'row',
      justifyContent: 'space-between',
      marginLeft: '10px',
      height: '100%',
      maxHeight: '300px',
      position: 'relative' as const,
    },
    sliderLabel: {
      writingMode: 'vertical-rl' as const,
      transform: 'rotate(-180deg)',
      fontSize: '14px',
      fontWeight: 500,
      textAlign: 'center' as const,
      whiteSpace: 'nowrap' as const,
      userSelect: 'none',
      cursor: 'default',
    },
  };

  return (
    <Box sx={styles.container}>
      {/* Chart SVG */}
      <svg
        ref={ref}
        style={styles.chart}
      />

      {/* Vertical Slider with Label on the Right */}
      <Box sx={styles.sliderContainer}>
        {/* Rotated Label */}
        <Box sx={styles.sliderLabel}>Number of Specializers</Box>

        {/* Vertical Slider Component */}
        <VerticalSlider
          min={0}
          max={1}
          step={0.1}
          onChange={handleSliderChange}
        />
      </Box>
    </Box>
  );
};

export default ParallelCoordinatesChart;

// Inline VerticalSlider Component
const VerticalSlider: React.FC<{
  min?: number;
  max?: number;
  step?: number;
  onChange?: (value: number) => void;
}> = ({
  min = 0,
  max = 1,
  step = 0.1,
  onChange,
}) => {
  const [value, setValue] = useState<number>((min + max) / 2);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = parseFloat(e.target.value);
    setValue(newValue);
    onChange?.(newValue);
  };

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      fontFamily: 'Inter, Roboto, sans-serif',
      padding: '10px 0',
    }}>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={handleChange}
        className="clean-vertical-slider"
        style={{
          writingMode: 'bt-lr',
          WebkitAppearance: 'slider-vertical',
          appearance: 'slider-vertical',
          height: '100%',
          width: '28px',
          background: 'transparent',
          margin: 0,
          padding: 0,
        }}
      />
      <div style={{
        marginTop: '10px',
        fontSize: '13px',
        fontWeight: 500,
        color: '#3f3f3f',
      }}>
        {value.toFixed(1)}
      </div>

      {/* CSS inside JSX for demo purposes */}
      <style>{`
        .clean-vertical-slider::-webkit-slider-thumb {
          -webkit-appearance: none;
          height: 16px;
          width: 16px;
          border-radius: 50%;
          background: transparent;
          border: 2px solid #3f51b5;
          box-shadow: 0 0 1px rgba(0, 0, 0, 0.2);
          margin-left: -6px;
          cursor: pointer;
        }

        .clean-vertical-slider::-webkit-slider-runnable-track {
          width: 4px;
          background: #e0e0e0;
          border-radius: 2px;
        }

        .clean-vertical-slider::-moz-range-thumb {
          height: 16px;
          width: 16px;
          border-radius: 50%;
          background: transparent;
          border: 2px solid #3f51b5;
          cursor: pointer;
        }

        .clean-vertical-slider::-moz-range-track {
          width: 4px;
          background: #e0e0e0;
          border-radius: 2px;
        }
      `}</style>
    </div>
  );
};