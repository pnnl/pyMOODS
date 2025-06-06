import React, { useState, useEffect, useRef } from 'react';
import * as d3 from 'd3';
import { Box, Typography, Select, MenuItem, FormControl, InputLabel } from '@mui/material';

// Import centralized config
import config from '../../config';
const { API_BASE_URL } = config;

interface LMPData {
  INTERVALSTARTTIME_GMT: string;
  LMP: string;
  [key: string]: any; // Allow extra fields like CaseStudy, Location, etc.
}

interface LMPPlotProps {
  useCase: string;
  filters: Record<string, string[]>;
}

const LMPPlot: React.FC<LMPPlotProps> = ({ useCase, filters }) => {
  const [data, setData] = useState<LMPData[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // State for filtering
  const caseStudies = [...new Set(data.map((d) => d['CaseStudy'] || 'default'))];
  const locations = [...new Set(data.map((d) => d['Location'] || 'default'))];

  const defaultCaseStudy = caseStudies.length > 0 ? caseStudies[0] : '';
  const defaultLocation = locations.length > 0 ? locations[0] : '';

  const [caseStudyFilter, setCaseStudyFilter] = useState(defaultCaseStudy);
  const [locationFilter, setLocationFilter] = useState(defaultLocation);
  const [selectedColumn, setSelectedColumn] = useState('LMP');

  const svgRef = useRef<SVGSVGElement | null>(null);
  const tooltipRef = useRef<HTMLDivElement | null>(null);

  // Apply filters
  const filteredData = data.filter(
    (d) =>
      (!caseStudyFilter || d['CaseStudy'] === caseStudyFilter) &&
      (!locationFilter || d['Location'] === locationFilter)
  );

  // Group by scenario ID (sim or identifier)
  const groupedBySim: Record<string, Array<{ time: number; value: number }>> = {};
  filteredData.forEach((d) => {
    const val = +d[selectedColumn];
    const sim = d['sim'] || d['INTERVALSTARTTIME_GMT'] || 'default';
    if (!groupedBySim[sim]) groupedBySim[sim] = [];
    groupedBySim[sim].push({
      time: new Date(d.INTERVALSTARTTIME_GMT).getTime(),
      value: isNaN(val) ? 0 : val,
    });
  });

  // Draw chart on filtered data change
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

    const allTimes = Object.values(groupedBySim).flatMap(series =>
      series.map(d => d.time)
    );
    const xDomain = d3.extent(allTimes) as [number, number]; // X-axis = time

    const yDomain = [
      0,
      d3.max(
        Object.values(groupedBySim).flatMap((arr) => arr.map((d) => d.value))
      ) || 100,
    ];

    const x = d3.scaleTime()
      .domain(xDomain)
      .range([margin.left, width - margin.right]);

    const y = d3.scaleLinear()
      .domain(yDomain)
      .range([height - margin.bottom, margin.top]);

    const xAxis = (g: any) =>
      g.attr('transform', `translate(0,${height - margin.bottom})`)
       .call(d3.axisBottom(x).tickFormat(d3.timeFormat("%H:%M")))
       .selectAll("text")
       .attr("font-size", "12px");

    const yAxis = (g: any) =>
      g.attr('transform', `translate(${margin.left},0)`)
       .call(d3.axisLeft(y))
       .selectAll("text")
       .attr("font-size", "12px");

    svg.append('g').call(xAxis);
    svg.append('g').call(yAxis);

    // Axis label
    svg.append("text")
      .attr("x", -height / 2)
      .attr("y", margin.left - 40)
      .attr("text-anchor", "middle")
      .attr("transform", "rotate(-90)")
      .attr("font-size", "14px")
      .text(selectedColumn);

    // Draw lines
    Object.entries(groupedBySim).forEach(([sim, values], i) => {
      const color = d3.schemeCategory10[i % 10];

      svg
        .append('path')
        .datum(values)
        .attr('fill', 'none')
        .attr('stroke', color)
        .attr('stroke-width', 1.5)
        .attr('d', d3.line().x((d: any) => x(d.time)).y((d: any) => y(d.value)))
        .on('mouseover', function (event, d) {
          d3.select(this).raise().attr('stroke-width', 2.5);
          showTooltip(event, sim, d[d.length - 1]);
        })
        .on('mousemove', function (event) {
          moveTooltip(event);
        })
        .on('mouseout', function () {
          hideTooltip();
          d3.select(this).attr('stroke-width', 1.5);
        });
    });
  };

  const showTooltip = (event: any, sim: string, point: any) => {
    if (!tooltipRef.current) return;
    const tooltip = tooltipRef.current;

    tooltip.style.opacity = '1';
    tooltip.style.left = `${event.pageX + 10}px`;
    tooltip.style.top = `${event.pageY + 10}px`;

    tooltip.innerHTML = `
      <strong>Scenario:</strong> ${sim}<br/>
      <strong>Time:</strong> ${new Date(point.time).toLocaleTimeString()}<br/>
      <strong>${selectedColumn}:</strong> ${point.value.toFixed(2)}
    `;
  };

  const moveTooltip = (event: any) => {
    if (!tooltipRef.current) return;
    tooltipRef.current.style.left = `${event.pageX + 10}px`;
    tooltipRef.current.style.top = `${event.pageY + 10}px`;
  };

  const hideTooltip = () => {
    if (!tooltipRef.current) return;
    tooltipRef.current.style.opacity = '0';
  };

  // Fetch LMP data
  useEffect(() => {
    if (!useCase) return;

    setLoading(true);
    setError(null);

    const queryParams = new URLSearchParams();

    Object.entries(filters).forEach(([key, values]) => {
      if (Array.isArray(values)) {
        values.forEach(value => queryParams.append(key, value));
      }
    });

    const url = `${API_BASE_URL}/api/lmp?${queryParams.toString()}&use_case=${useCase}`;
    console.log(url)

    fetch(url)
      .then(res => {
        if (!res.ok) throw new Error("Failed to fetch LMP data");
        return res.json();
      })
      .then(jsonData => {
        setData(jsonData.data || []);
      })
      .catch(err => {
        console.error('Error fetching LMP data:', err);
        setError("Failed to load LMP data.");
      })
      .finally(() => {
        setLoading(false);
      });
  }, [useCase, filters]);

  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h6" align="center">LMP Time Series</Typography>

      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, mb: 2 }}>
        <FormControl size="small">
          <InputLabel>Column</InputLabel>
          <Select
            value={selectedColumn}
            onChange={(e) => setSelectedColumn(e.target.value)}
            label="Column"
          >
            {Object.keys(data[0] || {})
              .filter(
                (key) =>
                  key !== 'INTERVALSTARTTIME_GMT' &&
                  key !== 'CaseStudy' &&
                  key !== 'Location'
              )
              .map((col) => (
                <MenuItem key={col} value={col}>
                  {col}
                </MenuItem>
              ))}
          </Select>
        </FormControl>

        {caseStudies.length > 1 && (
          <FormControl size="small">
            <InputLabel>Case Study</InputLabel>
            <Select
              value={caseStudyFilter}
              onChange={(e) => setCaseStudyFilter(e.target.value)}
              label="Case Study"
            >
              {caseStudies.map((cs) => (
                <MenuItem key={cs} value={cs}>
                  {cs}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        )}

        {locations.length > 1 && (
          <FormControl size="small">
            <InputLabel>Location</InputLabel>
            <Select
              value={locationFilter}
              onChange={(e) => setLocationFilter(e.target.value)}
              label="Location"
            >
              {locations.map((loc) => (
                <MenuItem key={loc} value={loc}>
                  {loc}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        )}
      </Box>

      <Box sx={{ textAlign: 'center' }}>
        <svg ref={svgRef}></svg>
        <div
          ref={tooltipRef}
          style={{
            position: 'absolute',
            padding: '8px 12px',
            background: '#fff',
            border: '1px solid #ccc',
            borderRadius: '4px',
            pointerEvents: 'none',
            opacity: 0,
            boxShadow: '0 2px 6px rgba(0,0,0,0.2)',
            fontSize: '12px',
            zIndex: 9999,
            minWidth: '120px',
            whiteSpace: 'nowrap',
          }}
        />
      </Box>

      {loading && !data.length && (
        <Typography>Loading LMP data...</Typography>
      )}

      {error && <Typography color="error">{error}</Typography>}
    </Box>
  );
};

export default LMPPlot;