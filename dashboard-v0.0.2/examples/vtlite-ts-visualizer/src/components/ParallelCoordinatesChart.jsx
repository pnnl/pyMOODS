import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';

// Sample Data
const rawData1 = {
  'Base,COTTONWOOD': {'Cable Material Cost($M)': 9.0, 'Battery Cost($M)': 13.0, 'Day-Ahead Revenue ($k)': 33.0, 'Real-Time Revenue ($k)': 11.0, 'Reserve WF Revenue ($k)': 3.0, 'Reserve ESS Revenue ($k)': 33.0},
  'Base,JOHNDAY': {'Cable Material Cost($M)': 26.0, 'Battery Cost($M)': 19.0, 'Day-Ahead Revenue ($k)': 27.0, 'Real-Time Revenue ($k)': 2.0, 'Reserve WF Revenue ($k)': 2.0, 'Reserve ESS Revenue ($k)': 28.0},
  'Base,MOSSLAND': {'Cable Material Cost($M)': 36.0, 'Battery Cost($M)': 12.0, 'Day-Ahead Revenue ($k)': 40.0, 'Real-Time Revenue ($k)': 12.0, 'Reserve WF Revenue ($k)': 4.0, 'Reserve ESS Revenue ($k)': 34.0},
  'Base,TESLA': {'Cable Material Cost($M)': 45.0, 'Battery Cost($M)': 21.0, 'Day-Ahead Revenue ($k)': 21.0, 'Real-Time Revenue ($k)': 1.0, 'Reserve WF Revenue ($k)': 1.0, 'Reserve ESS Revenue ($k)': 22.0},
  'Base,WCASCADE': {'Cable Material Cost($M)': 35.0, 'Battery Cost($M)': 11.0, 'Day-Ahead Revenue ($k)': 45.0, 'Real-Time Revenue ($k)': 14.0, 'Reserve WF Revenue ($k)': 5.0, 'Reserve ESS Revenue ($k)': 35.0},
  'No ESS,COTTONWOOD': {'Cable Material Cost($M)': 2.0, 'Battery Cost($M)': 3.0, 'Day-Ahead Revenue ($k)': 32.0, 'Real-Time Revenue ($k)': 25.0, 'Reserve WF Revenue ($k)': 8.0, 'Reserve ESS Revenue ($k)': 40.5},
  'No ESS,JOHNDAY': {'Cable Material Cost($M)': 20.0, 'Battery Cost($M)': 3.0, 'Day-Ahead Revenue ($k)': 26.0, 'Real-Time Revenue ($k)': 10.0, 'Reserve WF Revenue ($k)': 7.0, 'Reserve ESS Revenue ($k)': 40.5},
  'No ESS,MOSSLAND': {'Cable Material Cost($M)': 29.0, 'Battery Cost($M)': 3.0, 'Day-Ahead Revenue ($k)': 38.0, 'Real-Time Revenue ($k)': 26.0, 'Reserve WF Revenue ($k)': 9.0, 'Reserve ESS Revenue ($k)': 40.5},
  'No ESS,TESLA': {'Cable Material Cost($M)': 37.0, 'Battery Cost($M)': 3.0, 'Day-Ahead Revenue ($k)': 20.0, 'Real-Time Revenue ($k)': 6.0, 'Reserve WF Revenue ($k)': 6.0, 'Reserve ESS Revenue ($k)': 40.5},
  'No ESS,WCASCADE': {'Cable Material Cost($M)': 11.0, 'Battery Cost($M)': 3.0, 'Day-Ahead Revenue ($k)': 44.0, 'Real-Time Revenue ($k)': 30.0, 'Reserve WF Revenue ($k)': 10.0, 'Reserve ESS Revenue ($k)': 40.5},
  'No Reserve,COTTONWOOD': {'Cable Material Cost($M)': 1.0, 'Battery Cost($M)': 10.0, 'Day-Ahead Revenue ($k)': 28.0, 'Real-Time Revenue ($k)': 39.0, 'Reserve WF Revenue ($k)': 43.0, 'Reserve ESS Revenue ($k)': 40.5},
  'No Reserve,JOHNDAY': {'Cable Material Cost($M)': 19.0, 'Battery Cost($M)': 8.0, 'Day-Ahead Revenue ($k)': 22.0, 'Real-Time Revenue ($k)': 16.0, 'Reserve WF Revenue ($k)': 43.0, 'Reserve ESS Revenue ($k)': 40.5},
  'No Reserve,MOSSLAND': {'Cable Material Cost($M)': 28.0, 'Battery Cost($M)': 7.0, 'Day-Ahead Revenue ($k)': 34.0, 'Real-Time Revenue ($k)': 38.0, 'Reserve WF Revenue ($k)': 43.0, 'Reserve ESS Revenue ($k)': 40.5},
  'No Reserve,TESLA': {'Cable Material Cost($M)': 38.0, 'Battery Cost($M)': 6.0, 'Day-Ahead Revenue ($k)': 16.0, 'Real-Time Revenue ($k)': 13.0, 'Reserve WF Revenue ($k)': 43.0, 'Reserve ESS Revenue ($k)': 40.5},
  'No Reserve,WCASCADE': {'Cable Material Cost($M)': 10.0, 'Battery Cost($M)': 9.0, 'Day-Ahead Revenue ($k)': 39.0, 'Real-Time Revenue ($k)': 34.0, 'Reserve WF Revenue ($k)': 43.0, 'Reserve ESS Revenue ($k)': 40.5},
  'CCD18_3,COTTONWOOD': {'Cable Material Cost($M)': 4.0, 'Battery Cost($M)': 26.0, 'Day-Ahead Revenue ($k)': 30.0, 'Real-Time Revenue ($k)': 33.0, 'Reserve WF Revenue ($k)': 31.0, 'Reserve ESS Revenue ($k)': 24.0},
  'CCD18_3,JOHNDAY': {'Cable Material Cost($M)': 24.0, 'Battery Cost($M)': 31.0, 'Day-Ahead Revenue ($k)': 23.0, 'Real-Time Revenue ($k)': 8.0, 'Reserve WF Revenue ($k)': 21.0, 'Reserve ESS Revenue ($k)': 16.0},
  'CCD18_3,MOSSLAND': {'Cable Material Cost($M)': 31.0, 'Battery Cost($M)': 23.0, 'Day-Ahead Revenue ($k)': 35.0, 'Real-Time Revenue ($k)': 23.0, 'Reserve WF Revenue ($k)': 38.0, 'Reserve ESS Revenue ($k)': 25.0},
  'CCD18_3,TESLA': {'Cable Material Cost($M)': 39.0, 'Battery Cost($M)': 36.0, 'Day-Ahead Revenue ($k)': 18.0, 'Real-Time Revenue ($k)': 4.0, 'Reserve WF Revenue ($k)': 19.0, 'Reserve ESS Revenue ($k)': 13.0},
  'CCD18_3,WCASCADE': {'Cable Material Cost($M)': 13.0, 'Battery Cost($M)': 17.0, 'Day-Ahead Revenue ($k)': 41.0, 'Real-Time Revenue ($k)': 31.0, 'Reserve WF Revenue ($k)': 39.0, 'Reserve ESS Revenue ($k)': 29.0},
  'CCD18_5,COTTONWOOD': {'Cable Material Cost($M)': 6.0, 'Battery Cost($M)': 25.0, 'Day-Ahead Revenue ($k)': 29.0, 'Real-Time Revenue ($k)': 32.0, 'Reserve WF Revenue ($k)': 32.0, 'Reserve ESS Revenue ($k)': 23.0},
  'CCD18_5,JOHNDAY': {'Cable Material Cost($M)': 25.0, 'Battery Cost($M)': 30.0, 'Day-Ahead Revenue ($k)': 24.0, 'Real-Time Revenue ($k)': 7.0, 'Reserve WF Revenue ($k)': 22.0, 'Reserve ESS Revenue ($k)': 15.0},
  'CCD18_5,MOSSLAND': {'Cable Material Cost($M)': 30.0, 'Battery Cost($M)': 22.0, 'Day-Ahead Revenue ($k)': 36.0, 'Real-Time Revenue ($k)': 22.0, 'Reserve WF Revenue ($k)': 37.0, 'Reserve ESS Revenue ($k)': 26.0},
  'CCD18_5,TESLA': {'Cable Material Cost($M)': 40.0, 'Battery Cost($M)': 35.0, 'Day-Ahead Revenue ($k)': 17.0, 'Real-Time Revenue ($k)': 3.0, 'Reserve WF Revenue ($k)': 18.0, 'Reserve ESS Revenue ($k)': 14.0},
  'CCD18_5,WCASCADE': {'Cable Material Cost($M)': 15.0, 'Battery Cost($M)': 16.0, 'Day-Ahead Revenue ($k)': 42.0, 'Real-Time Revenue ($k)': 29.0, 'Reserve WF Revenue ($k)': 40.0, 'Reserve ESS Revenue ($k)': 30.0},
  'CCD18_8,COTTONWOOD': {'Cable Material Cost($M)': 7.0, 'Battery Cost($M)': 20.0, 'Day-Ahead Revenue ($k)': 31.0, 'Real-Time Revenue ($k)': 28.0, 'Reserve WF Revenue ($k)': 30.0, 'Reserve ESS Revenue ($k)': 27.0},
  'CCD18_8,JOHNDAY': {'Cable Material Cost($M)': 18.0, 'Battery Cost($M)': 28.0, 'Day-Ahead Revenue ($k)': 25.0, 'Real-Time Revenue ($k)': 9.0, 'Reserve WF Revenue ($k)': 15.0, 'Reserve ESS Revenue ($k)': 20.0},
  'CCD18_8,MOSSLAND': {'Cable Material Cost($M)': 27.0, 'Battery Cost($M)': 14.0, 'Day-Ahead Revenue ($k)': 37.0, 'Real-Time Revenue ($k)': 24.0, 'Reserve WF Revenue ($k)': 26.0, 'Reserve ESS Revenue ($k)': 31.0},
  'CCD18_8,TESLA': {'Cable Material Cost($M)': 44.0, 'Battery Cost($M)': 29.0, 'Day-Ahead Revenue ($k)': 19.0, 'Real-Time Revenue ($k)': 5.0, 'Reserve WF Revenue ($k)': 14.0, 'Reserve ESS Revenue ($k)': 18.0},
  'CCD18_8,WCASCADE': {'Cable Material Cost($M)': 17.0, 'Battery Cost($M)': 15.0, 'Day-Ahead Revenue ($k)': 43.0, 'Real-Time Revenue ($k)': 27.0, 'Reserve WF Revenue ($k)': 36.0, 'Reserve ESS Revenue ($k)': 32.0},
  'CCD22_3,COTTONWOOD': {'Cable Material Cost($M)': 3.0, 'Battery Cost($M)': 41.0, 'Day-Ahead Revenue ($k)': 8.0, 'Real-Time Revenue ($k)': 37.0, 'Reserve WF Revenue ($k)': 25.0, 'Reserve ESS Revenue ($k)': 6.0},
  'CCD22_3,JOHNDAY': {'Cable Material Cost($M)': 21.0, 'Battery Cost($M)': 43.0, 'Day-Ahead Revenue ($k)': 5.0, 'Real-Time Revenue ($k)': 17.0, 'Reserve WF Revenue ($k)': 16.0, 'Reserve ESS Revenue ($k)': 3.0},
  'CCD22_3,MOSSLAND': {'Cable Material Cost($M)': 34.0, 'Battery Cost($M)': 39.0, 'Day-Ahead Revenue ($k)': 10.0, 'Real-Time Revenue ($k)': 42.0, 'Reserve WF Revenue ($k)': 27.0, 'Reserve ESS Revenue ($k)': 8.0},
  'CCD22_3,TESLA': {'Cable Material Cost($M)': 42.0, 'Battery Cost($M)': 44.0, 'Day-Ahead Revenue ($k)': 1.0, 'Real-Time Revenue ($k)': 45.0, 'Reserve WF Revenue ($k)': 12.0, 'Reserve ESS Revenue ($k)': 1.0},
  'CCD22_3,WCASCADE': {'Cable Material Cost($M)': 14.0, 'Battery Cost($M)': 33.0, 'Day-Ahead Revenue ($k)': 13.0, 'Real-Time Revenue ($k)': 21.0, 'Reserve WF Revenue ($k)': 34.0, 'Reserve ESS Revenue ($k)': 10.0},
  'CCD22_5,COTTONWOOD': {'Cable Material Cost($M)': 5.0, 'Battery Cost($M)': 40.0, 'Day-Ahead Revenue ($k)': 7.0, 'Real-Time Revenue ($k)': 36.0, 'Reserve WF Revenue ($k)': 24.0, 'Reserve ESS Revenue ($k)': 5.0},
  'CCD22_5,JOHNDAY': {'Cable Material Cost($M)': 22.0, 'Battery Cost($M)': 42.0, 'Day-Ahead Revenue ($k)': 4.0, 'Real-Time Revenue ($k)': 18.0, 'Reserve WF Revenue ($k)': 17.0, 'Reserve ESS Revenue ($k)': 4.0},
  'CCD22_5,MOSSLAND': {'Cable Material Cost($M)': 32.0, 'Battery Cost($M)': 38.0, 'Day-Ahead Revenue ($k)': 11.0, 'Real-Time Revenue ($k)': 41.0, 'Reserve WF Revenue ($k)': 29.0, 'Reserve ESS Revenue ($k)': 7.0},
  'CCD22_5,TESLA': {'Cable Material Cost($M)': 41.0, 'Battery Cost($M)': 45.0, 'Day-Ahead Revenue ($k)': 2.0, 'Real-Time Revenue ($k)': 44.0, 'Reserve WF Revenue ($k)': 11.0, 'Reserve ESS Revenue ($k)': 2.0},
  'CCD22_5,WCASCADE': {'Cable Material Cost($M)': 12.0, 'Battery Cost($M)': 34.0, 'Day-Ahead Revenue ($k)': 12.0, 'Real-Time Revenue ($k)': 20.0, 'Reserve WF Revenue ($k)': 35.0, 'Reserve ESS Revenue ($k)': 11.0},
  'CCD22_8,COTTONWOOD': {'Cable Material Cost($M)': 8.0, 'Battery Cost($M)': 27.0, 'Day-Ahead Revenue ($k)': 9.0, 'Real-Time Revenue ($k)': 35.0, 'Reserve WF Revenue ($k)': 23.0, 'Reserve ESS Revenue ($k)': 17.0},
  'CCD22_8,JOHNDAY': {'Cable Material Cost($M)': 23.0, 'Battery Cost($M)': 32.0, 'Day-Ahead Revenue ($k)': 6.0, 'Real-Time Revenue ($k)': 15.0, 'Reserve WF Revenue ($k)': 20.0, 'Reserve ESS Revenue ($k)': 12.0},
  'CCD22_8,MOSSLAND': {'Cable Material Cost($M)': 33.0, 'Battery Cost($M)': 24.0, 'Day-Ahead Revenue ($k)': 14.0, 'Real-Time Revenue ($k)': 40.0, 'Reserve WF Revenue ($k)': 28.0, 'Reserve ESS Revenue ($k)': 19.0},
  'CCD22_8,TESLA': {'Cable Material Cost($M)': 43.0, 'Battery Cost($M)': 37.0, 'Day-Ahead Revenue ($k)': 3.0, 'Real-Time Revenue ($k)': 43.0, 'Reserve WF Revenue ($k)': 13.0, 'Reserve ESS Revenue ($k)': 9.0},
  'CCD22_8,WCASCADE': {'Cable Material Cost($M)': 16.0, 'Battery Cost($M)': 18.0, 'Day-Ahead Revenue ($k)': 15.0, 'Real-Time Revenue ($k)': 19.0, 'Reserve WF Revenue ($k)': 33.0, 'Reserve ESS Revenue ($k)': 21.0}
};

const rawData = {
    'Base,COTTONWOOD': {
      'Cable Material Cost($M)': 261.81824605164803,
      'Battery Cost($M)': 32.1840806,
      'Day-Ahead Revenue ($k)': 1040.7599342383824,
      'Real-Time Revenue ($k)': 29.040111297712404,
      'Reserve WF Revenue ($k)': 2.5297679920411227,
      'Reserve ESS Revenue ($k)': 0.7385134126741629
    },
    'Base,JOHNDAY': {
      'Cable Material Cost($M)': 358.91598635692804,
      'Battery Cost($M)': 41.785961,
      'Day-Ahead Revenue ($k)': 1303.2109905740886,
      'Real-Time Revenue ($k)': 45.32862173482326,
      'Reserve WF Revenue ($k)': 3.1924984864127453,
      'Reserve ESS Revenue ($k)': 0.959951051
    },
    'Base,MOSSLAND': {
      'Cable Material Cost($M)': 533.6071209,
      'Battery Cost($M)': 32.006268,
      'Day-Ahead Revenue ($k)': 919.3376414105542,
      'Real-Time Revenue ($k)': 28.506600070024582,
      'Reserve WF Revenue ($k)': 2.24491459,
      'Reserve ESS Revenue ($k)': 0.7335952829056427
    },
    'Base,TESLA': {
      'Cable Material Cost($M)': 974.931412339456,
      'Battery Cost($M)': 46.9425264,
      'Day-Ahead Revenue ($k)': 1422.478137892257,
      'Real-Time Revenue ($k)': 49.483370256586774,
      'Reserve WF Revenue ($k)': 3.4734853641236563,
      'Reserve ESS Revenue ($k)': 1.0840994563741675
    },
    'Base,WCASCADE': {
      'Cable Material Cost($M)': 440.1904211,
      'Battery Cost($M)': 26.67189,
      'Day-Ahead Revenue ($k)': 876.8024860587059,
      'Real-Time Revenue ($k)': 25.572794112443862,
      'Reserve WF Revenue ($k)': 2.0815707243130763,
      'Reserve ESS Revenue ($k)': 0.6050571841257946
    }
  };

// Flatten and Rank Function
const rankData = (rawData) => {
    const flatData = Object.entries(rawData).map(([key, values]) => {
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
  
  const ParallelCoordinatesChart = () => {
    const ref = useRef();
    const { rankedData, numericColumns } = rankData(rawData);
  
    useEffect(() => {
      draw();
    }, []);
  
    const draw = () => {
      const margin = { top: 50, right: 40, bottom: 120, left: 80 };
      const width = 900 - margin.left - margin.right;
      const height = 400 - margin.top - margin.bottom;
  
      const svg = d3.select(ref.current)
        .attr("viewBox", [0, 0, width + margin.left + margin.right, height + margin.top + margin.bottom])
        .attr("preserveAspectRatio", "xMidYMid meet")
        .style('background', '#fff');
  
      svg.select('g').remove();
      const g = svg.append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);
  
      const rankColumns = numericColumns.map(c => `${c}_rank`);
  
      // Get all unique configurations
        const configs = [...new Set(rankedData.map(d => d.config))];

        // Create a color scale
        const colorScale = d3.scaleOrdinal(d3.schemeCategory10)
        .domain(configs);

        // Optional: Use more colors if you have many configs
        // const colorScale = d3.scaleOrdinal(d3.schemeTableau10).domain(configs);

        // If you still want to access it like an object map:
        const colorMap = Object.fromEntries(configs.map(config => [config, colorScale(config)]));
  
      // Create scales
      const yScales = {};
      const xScale = d3.scalePoint()
        .domain(rankColumns)
        .range([0, width])
        .padding(1); // increase spacing between axes
  
      rankColumns.forEach(col => {
        const extent = d3.extent(rankedData, d => d[col]);
        yScales[col] = d3.scaleLinear()
          .domain(extent)
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
      const lines = g.selectAll('.line')
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
  
      // Only draw y-axis on first dimension
      const firstDim = rankColumns[0];
      // Draw leftmost y-axis without text labels
        const yAxisGroup = g.append('g')
        .attr('transform', `translate(${xScale(firstDim)},0)`)
        .call(d3.axisLeft(yScales[firstDim]).ticks(5));

        // Remove text labels from the y-axis
        yAxisGroup.selectAll('text').remove();

        // Optional: Keep ticks only (thin cleanup)
        yAxisGroup.selectAll('.domain').remove(); // optional: remove domain line if needed
  
    //   g.append('text')
    //     .attr('transform', 'rotate(-90)')
    //     .attr('y', -40)
    //     .attr('x', -height / 2)
    //     .attr('dy', '1em')
    //     .style('text-anchor', 'middle')
    //     .style('font-size', '16px')
    //     .text('Rank');
  
      // Axis lines only (no ticks)
      rankColumns.forEach((col, i) => {
        g.append('line')
          .attr('x1', xScale(col))
          .attr('x2', xScale(col))
          .attr('y1', 0)
          .attr('y2', height)
          .attr('stroke', '#eee');
      });
  
      const wrapText = (text, width) => {
        text.each(function () {
          const text = d3.select(this);
          let words = text.text().split(/\s+/).reverse();
          let word;
          let line = [];
          let lineNumber = 0;
          const lineHeight = 1.2; // controls vertical spacing
          const y = text.attr('y');
          const x = text.attr('x') || 0;
      
          text.text(null); // clear existing content
      
          let tspan = text.append('tspan')
            .attr('x', x)
            .attr('y', y)
            .attr('dy', '0em'); // anchor first line at top
      
          while ((word = words.pop())) {
            line.push(word);
            tspan.text(line.join(' '));
            if (tspan.node().getComputedTextLength() > width) {
              line.pop();
              tspan.text(line.join(' '));
              line = [word];
              lineNumber++;
              tspan = text.append('tspan')
                .attr('x', x)
                .attr('y', y)
                .attr('dy', `${lineNumber * lineHeight}em`) // relative to top
                .text(word);
            }
          }
        });
      };      
  
      // Add metric names at the bottom with wrapping
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
        .call(wrapText, 60); // wrap every 60px
    };
  
    return <svg ref={ref}></svg>;
  };
  
  export default ParallelCoordinatesChart;