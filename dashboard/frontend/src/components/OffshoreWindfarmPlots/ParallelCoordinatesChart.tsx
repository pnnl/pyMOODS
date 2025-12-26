import React, { useEffect, useRef, useState } from 'react';
import { Box } from '@mui/material';
import * as d3 from 'd3';

// Define types
interface RankDict {
  [key: string]: Record<string, number>;
}

interface ParallelCoordinatesChartProps {
  ranks: RankDict;
  objectiveColorMap: Record<string, string>;
}

const ParallelCoordinatesChart: React.FC<ParallelCoordinatesChartProps> = ({ ranks, objectiveColorMap }) => {
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
    }) as Array<{ config: string; site: string; [key: string]: any }>;

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
    const height = 240 - margin.top - margin.bottom;

    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    const { rankedData, numericColumns } = processData();
    if (!rankedData.length) return;

    const rankColumns = numericColumns.map(c => `${c}_rank`);

    // Cable Material Cost ($M): #4ECDC4
    // Battery Cost ($M): #FF6B6B
    // Day-Ahead Revenue ($k): #96A6C5
    // Real-Time Revenue ($k): #45B7D1
    // Reserve WF Revenue ($k): #FFA07AW
    // Reserve ESS Revenue ($k): #FAC84D

    // Color scale by configuration using consistent colors
    const configs = [...new Set(rankedData.map(d => d.config))];
    const colorPalette = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96A6C5', '#FAC84D', '#FFA07A'];
    const colorScale = d3.scaleOrdinal(colorPalette).domain(configs);
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
      .style('opacity', 0)
      .style('color', '#000')
      .style('color-scheme', 'light');

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
          // .x(p => xScale(p[0]))
          // .y(p => yScales[p[0]](d[p[0]]))
          // (rankColumns.map(dim => [dim, d[dim]]))

          // fixing typescript errors
          .x((_, i) => xScale(rankColumns[i]) || 0)
          .y((_, i) => yScales[rankColumns[i]](d[rankColumns[i]]))
          (rankColumns.map(dim => [xScale(dim) || 0, yScales[dim](d[dim])]))
      )
      .on('mouseover', function(event, d) {
        d3.select(this).attr('stroke-width', 4);
        tooltip.transition().duration(200).style('opacity', .9);
        tooltip.html(`<span style="color: #000;">${d.config} - ${d.site}</span>`)
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
        .attr('x1', xScale(col) ?? 0)
        .attr('x2', xScale(col) ?? 0)
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
      .attr('x', d => xScale(d) || 0)
      .attr('y', height + 20)
      .attr('text-anchor', 'middle')
      .style('font-size', '11px')
      .style('font-family', 'Inter, Roboto, sans-serif')
      .style('font-weight', '500')
      .style('fill',(d,i) => objectiveColorMap[numericColumns[i]] || '#213547')
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
      // Clean up any existing tooltips
      d3.selectAll('.tooltip').remove();
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
      flexDirection: 'column',
      alignItems: 'stretch', // Full width
      width: '100%',
      minHeight: '280px',
      position: 'relative',
    },
    sliderContainer: {
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      gap: '4px'
    },
    chart: {
      flexGrow: 1,
      height: 'auto',
      minHeight: '280px',
    },
  };

  return (
    <Box sx={styles.container}>
      {/* Horizontal Slider with Label on the Right */}
      <Box sx={styles.sliderContainer}>
        {/* Horizontal Slider Component */}
        <HorizontalSlider
          min={1}
          max={10}
          step={1}
          onChange={handleSliderChange}
        />
      </Box>
  
      {/* Chart SVG */}
      <svg
        ref={ref}
        style={styles.chart}
      />
    </Box>
  );
};

export default ParallelCoordinatesChart;

// Inline VerticalSlider Component
const HorizontalSlider: React.FC<{
  min?: number;
  max?: number;
  step?: number;
  onChange?: (value: number) => void;
}> = ({
  min = 1,
  max = 10,
  step = 1,
  onChange,
}) => {
  const [value, setValue] = useState<number>(Math.round((min + max) / 2));

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = parseFloat(e.target.value);
    setValue(newValue);
    onChange?.(newValue);
  };

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        fontFamily: 'Inter, Roboto, sans-serif',
        width: '90%',
        padding: 0,
        margin: 0,
      }}
    >
      <div
        style={{
          marginTop: 0,
          fontSize: '16px', 
          fontWeight: 500, 
          color:'#213547',
          fontFamily: 'Inter,system-ui, Avenir, Helvetica,Arial, sans-serif',
          colorScheme: 'light',
        }}
      >
        Minimum Number of Specializers: {value.toFixed(0)}
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={handleChange}
        className="clean-horizontal-slider"
        style={{
          width: '90%',
          height: '28px',
          background: 'transparent',
          margin: 0,
          padding: 0,
        }}
      />
      

      <style>{`
        .clean-horizontal-slider::-webkit-slider-thumb {
          -webkit-appearance: none;
          height: 16px;
          width: 16px;
          border-radius: 50%;
          background: transparent;
          border: 2px solid #3f51b5;
          box-shadow: 0 0 1px rgba(0, 0, 0, 0.2);
          cursor: pointer;
          margin-top: -6px; /* Align thumb */
        }

        .clean-horizontal-slider::-webkit-slider-runnable-track {
          height: 4px;
          background: #e0e0e0;
          border-radius: 2px;
        }

        .clean-horizontal-slider::-moz-range-thumb {
          height: 16px;
          width: 16px;
          border-radius: 50%;
          background: transparent;
          border: 2px solid #3f51b5;
          cursor: pointer;
        }

        .clean-horizontal-slider::-moz-range-track {
          height: 4px;
          background: #e0e0e0;
          border-radius: 2px;
        }
      `}</style>
    </div>
  );
};

