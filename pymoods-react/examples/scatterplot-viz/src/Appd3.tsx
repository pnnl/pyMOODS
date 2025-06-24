import React, { useEffect, useState } from 'react';

// Import only what we need from d3
import {
  select,
  min,
  max,
  scaleLinear,
  axisBottom,
  axisLeft,
  scaleOrdinal,
  schemeCategory10
} from 'd3';

type DataItem = {
  [key: string]: number | string;
};

const App: React.FC = () => {
  const [data, setData] = useState<DataItem[]>([]);
  const [columns, setColumns] = useState<string[]>([]);
  const [numericCols, setNumericCols] = useState<string[]>([]);
  const [nonNumericCols, setNonNumericCols] = useState<string[]>([]);

  const [xAxis, setXAxis] = useState('x_coord');
  const [yAxis, setYAxis] = useState('y_coord');
  const [colorBy, setColorBy] = useState('label');

  const svgRef = React.useRef<SVGSVGElement | null>(null);

  // Load and parse CSV
  useEffect(() => {
    fetch('/scenarios.csv')
      .then((res) => res.text())
      .then((csvText) => {
        const rows = csvText.trim().split('\n');
        const headers = rows[0].split(',');
        const parsedData = rows.slice(1).map(row => {
          const values = row.split(',');
          const obj: Record<string, number | string> = {};
          headers.forEach((header, i) => {
            const value = values[i];
            obj[header] = isNaN(+value) ? value : +value;
          });
          return obj;
        });

        setData(parsedData);
        setColumns(headers);

        const numeric = headers.filter(h => typeof parsedData[0][h] === 'number');
        const nonNumeric = headers.filter(h => typeof parsedData[0][h] !== 'number');

        setNumericCols(numeric);
        setNonNumericCols(nonNumeric);
      });
  }, []);

  // Draw chart when any config changes
  useEffect(() => {
    if (!data.length || !svgRef.current) return;

    const width = 900;
    const height = 500;
    const margin = { top: 40, right: 40, bottom: 80, left: 80 };

    const svg = select(svgRef.current)
      .attr('width', width)
      .attr('height', height)
      .style('background', '#f9f9f9');

    svg.selectAll('*').remove(); // Clear previous content

    const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`);

    const xMin = min(data, d => d[xAxis] as number) || 0;
    const xMax = max(data, d => d[xAxis] as number) || 1;
    const yMin = min(data, d => d[yAxis] as number) || 0;
    const yMax = max(data, d => d[yAxis] as number) || 1;

    const xScale = scaleLinear()
      .domain([xMin - (xMax - xMin) * 0.1, xMax + (xMax - xMin) * 0.1])
      .range([0, width - margin.left - margin.right]);

    const yScale = scaleLinear()
      .domain([yMin - (yMax - yMin) * 0.1, yMax + (yMax - yMin) * 0.1])
      .range([height - margin.top - margin.bottom, 0]);

    const uniqueColors = Array.from(new Set(data.map(d => d[colorBy] as string)));
    const colorScale = scaleOrdinal(schemeCategory10).domain(uniqueColors);

    // Axes
    g.append('g')
      .attr('transform', `translate(0,${height - margin.top - margin.bottom})`)
      .call(axisBottom(xScale));

    g.append('g')
      .call(axisLeft(yScale));

    // Axis labels
    g.append('text')
      .attr('x', width / 2)
      .attr('y', height - margin.bottom / 2 + 20)
      .text(xAxis)
      .style('text-anchor', 'middle');

    g.append('text')
      .attr('transform', 'rotate(-90)')
      .attr('x', -height / 2)
      .attr('y', -margin.left + 20)
      .text(yAxis)
      .style('text-anchor', 'middle');

    // Circles
    g.selectAll('circle')
      .data(data)
      .enter()
      .append('circle')
      .attr('cx', d => xScale(d[xAxis] as number))
      .attr('cy', d => yScale(d[yAxis] as number))
      .attr('r', 6)
      .attr('fill', d => colorScale(d[colorBy] as string))
      .on('mouseover', function (event, d) {
        select('#tooltip')
          .style('left', event.pageX + 'px')
          .style('top', event.pageY - 30 + 'px')
          .style('display', 'block')
          .html(
            Object.entries(d)
              .map(([k, v]) => `<strong>${k}:</strong> ${v}<br/>`)
              .join('')
          );
      })
      .on('mouseout', () => {
        select('#tooltip').style('display', 'none');
      });

    // Legend
    const legend = g.append('g')
      .attr('transform', `translate(${width - 150}, 0)`);

    uniqueColors.forEach((category, i) => {
      const legendRow = legend.append('g')
        .attr('transform', `translate(0, ${i * 20})`);

      legendRow.append('rect')
        .attr('width', 15)
        .attr('height', 15)
        .attr('fill', colorScale(category));

      legendRow.append('text')
        .attr('x', 20)
        .attr('y', 12)
        .text(category);
    });

  }, [data, xAxis, yAxis, colorBy]);

  return (
    <div style={{ padding: '20px' }}>
      <h1>Interactive D3 Scatter Plot</h1>

      <div>
        <label>X-Axis:</label>
        <select value={xAxis} onChange={(e) => setXAxis(e.target.value)}>
          {numericCols.map(col => (
            <option key={col} value={col}>{col}</option>
          ))}
        </select>
      </div>

      <div>
        <label>Y-Axis:</label>
        <select value={yAxis} onChange={(e) => setYAxis(e.target.value)}>
          {numericCols.map(col => (
            <option key={col} value={col}>{col}</option>
          ))}
        </select>
      </div>

      <div>
        <label>Color By:</label>
        <select value={colorBy} onChange={(e) => setColorBy(e.target.value)}>
          {nonNumericCols.map(col => (
            <option key={col} value={col}>{col}</option>
          ))}
        </select>
      </div>

      <div style={{ height: '600px', width: '100%' }}>
        <svg ref={svgRef}></svg>
        <div id="tooltip" style={{
          position: 'absolute',
          display: 'none',
          background: 'white',
          border: '1px solid #ccc',
          padding: '8px',
          pointerEvents: 'none'
        }}></div>
      </div>
    </div>
  );
};

export default App;