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

interface Solution {
  [key: string]: any;
}

interface LMPPlotProps {
  useCase: string;
  filters: Record<string, string[]>;
  selectedSolution?: Solution;
}

const LMPPlot: React.FC<LMPPlotProps> = ({ useCase, filters, selectedSolution }) => {
  const [data, setData] = useState<LMPData[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [tooltipVisible, setTooltipVisible] = useState(false);
  const [tooltipData, setTooltipData] = useState({ x: 0, y: 0, sim: '', value: '', time: '' });

  // State for filtering
  const caseStudies = [...new Set(data.map((d) => d['CaseStudy'] || 'default'))];
  const defaultCaseStudy = caseStudies.length > 0 ? caseStudies[0] : '';
  const [caseStudyFilter, setCaseStudyFilter] = useState(defaultCaseStudy);
  
  const [selectedColumn, setSelectedColumn] = useState<string>('');

  const svgRef = useRef<SVGSVGElement | null>(null);
  const tooltipRef = useRef<HTMLDivElement | null>(null);

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

  const numericColumns = React.useMemo(() => {
    if (!data.length) return [];
  
    const firstRow = data[0];
    return Object.keys(firstRow).filter(
      key =>
        key !== 'INTERVALSTARTTIME_GMT' &&
        key !== 'CaseStudy' &&
        key !== 'Location' &&
        !isNaN(parseFloat(firstRow[key]))
    );
  }, [data]);

  useEffect(() => {
    if (numericColumns.length > 0 && !selectedColumn) {
      setSelectedColumn(numericColumns[0]);
    }
  }, [numericColumns, selectedColumn]);

  // Apply filters
  const filteredData = data.filter(
    (d) =>
      (!selectedSolution || d['Case Study'] === selectedSolution["Case Study"]) &&
      (!selectedSolution || d['Location'] === selectedSolution["Location"])
  );
  
  const groupedBySim: Record<string, Array<{ time: number; value: number }>> = {};

  filteredData.forEach((d) => {
    const rawValue = d[selectedColumn];

    let val;

    if (typeof rawValue === 'string') {
      // Remove non-numeric characters except . and -
      const cleaned = rawValue.replace(/[^0-9.-]/g, '');

      // Check if cleaned string is a valid number
      val = cleaned && !isNaN(cleaned) && isFinite(cleaned) ? parseFloat(cleaned) : NaN;

    } else if (typeof rawValue === 'number') {
      val = rawValue;
    } else {
      val = NaN;
    }

    const sim = d['sim'] || d['INTERVALSTARTTIME_GMT'] || 'default';
    const time = d['time'];

    if (!groupedBySim[sim]) groupedBySim[sim] = [];
    groupedBySim[sim].push({
      time,
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
    <Box sx={{ p: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'center', mb: 2, width: '100%' }}>
        <Box sx={{ width: '50%', maxWidth: 400 }}>
          <FormControl size="small" fullWidth>
            <InputLabel style={{fontSize: '0.9rem', fontWeight:'bold', fontFamily:'Inter, system-ui, Avenir, Helvetica, Arial, sans-serif'}}>Column</InputLabel>
            <Select
              value={selectedColumn}
              onChange={(e) => setSelectedColumn(e.target.value)}
              label="Column"
            >
              {numericColumns.map((col) => (
                <MenuItem key={col} value={col}>
                  {col}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Box>

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
      </Box>

      <Box sx={{ textAlign: 'center' }}>
        <svg ref={svgRef}></svg>
        {tooltipVisible && (
          <div
            ref={tooltipRef}
            style={{
              position: 'absolute',
              left: `${
                tooltipRef.current
                  ? Math.min(
                      tooltipData.x + 10,
                      window.innerWidth - tooltipRef.current.offsetWidth - 10
                    )
                  : tooltipData.x + 10
              }px`,
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
              textAlign: 'left',
              maxWidth: '300px',
            }}
          >
            <strong>Scenario:</strong> {tooltipData.sim}
            <br />
            <strong>Time:</strong> {tooltipData.time}
            <br />
            <strong>{selectedColumn}:</strong> {tooltipData.value}
          </div>
        )}

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