// src/components/TimeSeriesChart.jsx
import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';

const TimeSeriesChart = ({ data }) => {
  const svgRef = useRef(null);
  const [tooltipVisible, setTooltipVisible] = useState(false);
  const [tooltipData, setTooltipData] = useState({ x: 0, y: 0, sim: '', value: '', time: '' });

  // Get unique values for filters
  const caseStudies = [...new Set(data.map((d) => d['CaseStudy']))];
  const locations = [...new Set(data.map((d) => d['Location']))];

  const [selectedColumn, setSelectedColumn] = useState('ChS');
  const defaultCaseStudy = caseStudies.length > 0 ? caseStudies[0] : '';
  const defaultLocation = locations.length > 0 ? locations[0] : '';

  const [caseStudyFilter, setCaseStudyFilter] = useState(defaultCaseStudy);
  const [locationFilter, setLocationFilter] = useState(defaultLocation);

  // Apply filters
  const filteredData = data.filter(
    (d) =>
      (!caseStudyFilter || d['CaseStudy'] === caseStudyFilter) &&
      (!locationFilter || d['Location'] === locationFilter)
  );

  // Group by scenario ID (sim)
  const groupedBySim = {};
  filteredData.forEach((d) => {
    const val = +d[selectedColumn];
    if (!groupedBySim[d.sim]) groupedBySim[d.sim] = [];
    groupedBySim[d.sim].push({ time: d.time, value: isNaN(val) ? 0 : val });
  });

  useEffect(() => {
    drawChart();
  }, [filteredData, selectedColumn]);

  const drawChart = () => {
    const width = 700;
    const height = 300;
    const margin = { top: 20, right: 30, bottom: 40, left: 60 };

    if (!svgRef.current) return;

    const svg = d3.select(svgRef.current).attr('width', width).attr('height', height);
    svg.selectAll('*').remove(); // Clear previous chart

    // Get all unique time points and sort them
    const allTimes = Object.values(groupedBySim).flatMap(series =>
      series.map(d => d.time)
    );
    const xDomain = d3.extent(allTimes); // X-axis = time

    // Y-axis = selected column value
    const yDomain = [
      0,
      d3.max(
        Object.values(groupedBySim).flatMap((arr) => arr.map((d) => d.value))
      ) || 100,
    ];

    const x = d3.scaleLinear()
      .domain(xDomain)
      .range([margin.left, width - margin.right]);

    const y = d3.scaleLinear()
      .domain(yDomain)
      .range([height - margin.bottom, margin.top]);

    // Create axes with larger tick labels
    const xAxis = (g) =>
      g.attr('transform', `translate(0,${height - margin.bottom})`)
       .call(d3.axisBottom(x))
       .selectAll("text")
       .attr("font-size", "16px");

    const yAxis = (g) =>
      g.attr('transform', `translate(${margin.left},0)`)
       .call(d3.axisLeft(y))
       .selectAll("text")
       .attr("font-size", "16px");

    svg.append('g').call(xAxis);
    svg.append('g').call(yAxis);

    // Axis labels
    // svg.append("text")
    //   .attr("x", width / 2)
    //   .attr("y", height - 5)
    //   .attr("text-anchor", "middle")
    //   .attr("font-size", "18px")
    //   .text("Time");

    svg.append("text")
      .attr("x", -height / 2)
      .attr("y", margin.left - 40)
      .attr("text-anchor", "middle")
      .attr("transform", "rotate(-90)")
      .attr("font-size", "18px")
      .text(selectedColumn);

    // Draw lines
    Object.entries(groupedBySim).forEach(([sim, values]) => {
      svg
        .append('path')
        .datum(values)
        .attr('fill', 'none')
        .attr('stroke', 'lightgrey')
        .attr('stroke-width', 1.5)
        .attr('d', d3.line().x((d) => x(d.time)).y((d) => y(d.value)))
        .on('mouseover', function (event, d) {
          d3.select(this)
            .raise()
            .attr('stroke', 'steelblue');
        
          const [mouseX, mouseY] = d3.pointer(event, svgRef.current);
          const invertX = x.invert(mouseX);
          const closest = d.reduce((a, b) => {
            return Math.abs(a.time - invertX) < Math.abs(b.time - invertX) ? a : b;
          });
        
          setTooltipData({
            x: mouseX,
            y: mouseY,
            sim: sim,
            value: closest.value.toFixed(4),
            time: closest.time.toFixed(2),
          });
          setTooltipVisible(true);
        })
        .on('mousemove', function (event) {
          const [mouseX, mouseY] = d3.pointer(event, svgRef.current);
          setTooltipData((prev) => ({
            ...prev,
            x: mouseX,
            y: mouseY,
          }));
        })
        .on('mouseout', function () {
          d3.select(this).attr('stroke', 'lightgrey');
          setTooltipVisible(false);
        });
    });
  };

  return (
    <div style={{ padding: '20px' }}>
      <div
        style={{
          maxWidth: '900px',
          margin: '0 auto',
          backgroundColor: '#f9f9f9',
          borderRadius: '10px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
          padding: '20px',
        }}
      >
        <h2 style={{ textAlign: 'center', marginBottom: '20px' }}>Time Series Visualizer</h2>

        <div
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: '20px',
            justifyContent: 'center',
            marginBottom: '20px',
          }}
        >
          <label style={{ fontSize: '14px' }}>
            Select Column:
            <select
              value={selectedColumn}
              onChange={(e) => setSelectedColumn(e.target.value)}
              style={{
                marginLeft: '10px',
                padding: '6px 12px',
                borderRadius: '4px',
                border: '1px solid #ccc',
              }}
            >
              {Object.keys(data[0])
                .filter(
                  (key) =>
                    key !== 'config' &&
                    key !== 'time' &&
                    key !== 'CaseStudy' &&
                    key !== 'Location'
                )
                .map((col) => (
                  <option key={col} value={col}>
                    {col}
                  </option>
                ))}
            </select>
          </label>

          {/* Case Study Dropdown */}
          <label style={{ fontSize: '14px' }}>
            Case Study:
            <select
              value={caseStudyFilter}
              onChange={(e) => setCaseStudyFilter(e.target.value)}
              style={{
                marginLeft: '10px',
                padding: '6px 12px',
                borderRadius: '4px',
                border: '1px solid #ccc',
              }}
            >
              {caseStudies.map((cs) => (
                <option key={cs} value={cs}>
                  {cs}
                </option>
              ))}
            </select>
          </label>

          {/* Location Dropdown */}
          <label style={{ fontSize: '14px' }}>
            Location:
            <select
              value={locationFilter}
              onChange={(e) => setLocationFilter(e.target.value)}
              style={{
                marginLeft: '10px',
                padding: '6px 12px',
                borderRadius: '4px',
                border: '1px solid #ccc',
              }}
            >
              {locations.map((loc) => (
                <option key={loc} value={loc}>
                  {loc}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div
          style={{
            position: 'relative',
            textAlign: 'center',
            border: '1px solid #ddd',
            borderRadius: '8px',
            background: '#fff',
            padding: '10px',
            boxShadow: '0 2px 6px rgba(0,0,0,0.05)',
          }}
        >
          <svg ref={svgRef}></svg>

          {tooltipVisible && (
            <div
              style={{
                position: 'absolute',
                left: `${tooltipData.x + 10}px`,
                top: `${tooltipData.y + 10}px`,
                background: '#fff',
                border: '1px solid #ccc',
                padding: '8px 14px',
                borderRadius: '6px',
                boxShadow: '0 4px 10px rgba(0,0,0,0.2)',
                pointerEvents: 'none',
                fontSize: '14px',
                zIndex: 9999,
                minWidth: '120px',
                whiteSpace: 'nowrap',
              }}
            >
              <strong>Scenario:</strong> {tooltipData.sim}
              <br />
              <strong>Time:</strong> {tooltipData.time}
              <br />
              <strong>{selectedColumn}:</strong> {tooltipData.value}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default TimeSeriesChart;