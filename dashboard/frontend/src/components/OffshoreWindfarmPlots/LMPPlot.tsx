import React, { useState, useEffect, useRef } from "react";
import * as d3 from "d3";
import {
  Box,
  Typography,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
} from "@mui/material";

// Import centralized config
import config from "../../config";
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

const LMPPlot: React.FC<LMPPlotProps> = ({
  useCase,
  filters,
  selectedSolution,
}) => {
  const [data, setData] = useState<LMPData[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [tooltipVisible, setTooltipVisible] = useState(false);
  const [tooltipData, setTooltipData] = useState({
    x: 0,
    y: 0,
    sim: "",
    value: "",
    time: "",
  });

  // State for filtering
  const caseStudies = [...new Set(data.map((d) => d['CaseStudy'] || 'default'))];
  const defaultCaseStudy = caseStudies.length > 0 ? caseStudies[0] : '';
  const [caseStudyFilter, setCaseStudyFilter] = useState(defaultCaseStudy);
  
  const [selectedColumn, setSelectedColumn] = useState<string>('');

  const svgRef = useRef<SVGSVGElement | null>(null);
  const tooltipRef = useRef<HTMLDivElement | null>(null);

  // Helper function to format dollar amounts
  const formatDollarValue = (columnName: string, value: number) => {
    // Check if the column name indicates a dollar amount
    const isDollarField = /(\$|cost|price|revenue|budget|capex|opex|lcoe|npv|profit|income|expense|lmp)/i.test(columnName);
    
    if (isDollarField) {
      // Round to nearest hundredth for currency display
      return `$${value.toFixed(2)}`;
    }
    
    // For non-dollar numeric values, check if they have many decimal places and round appropriately
    if (!Number.isInteger(value)) {
      const stringValue = value.toString();
      const decimalPlaces = stringValue.split('.')[1]?.length || 0;
      if (decimalPlaces > 4) {
        return value.toFixed(2);
      } else if (decimalPlaces > 2) {
        return value.toFixed(4);
      }
    }
    
    return value.toString();
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
      (key) =>
        key !== "INTERVALSTARTTIME_GMT" &&
        key !== "CaseStudy" &&
        key !== "Location" &&
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
      (!selectedSolution ||
        d["Case Study"] === selectedSolution["Case Study"]) &&
      (!selectedSolution || d["Location"] === selectedSolution["Location"])
  );

  const groupedBySim: Record<
    string,
    Array<{ time: number; value: number }>
  > = {};

  filteredData.forEach((d) => {
    const rawValue = d[selectedColumn];

    let val;

    if (typeof rawValue === "string") {
      // Remove non-numeric characters except . and -
      const cleaned = rawValue.replace(/[^0-9.-]/g, "");

      // Check if cleaned string is a valid number
      val =
        cleaned && !isNaN(cleaned) && isFinite(cleaned)
          ? parseFloat(cleaned)
          : NaN;
    } else if (typeof rawValue === "number") {
      val = rawValue;
    } else {
      val = NaN;
    }

    const sim = d["sim"] || d["INTERVALSTARTTIME_GMT"] || "default";
    const time = d["time"];

    if (!groupedBySim[sim]) groupedBySim[sim] = [];
    groupedBySim[sim].push({
      time,
      value: isNaN(val) ? 0 : val,
    });
  });

  // Draw chart on filtered data change
  useEffect(() => {
    const resizeObserver = new ResizeObserver(() => drawChart());
    if (svgRef.current?.parentElement) {
      resizeObserver.observe(svgRef.current.parentElement);
    }
    return () => resizeObserver.disconnect();
  }, [filteredData, selectedColumn]);  

  const drawChart = () => {
    const svgElement = svgRef.current;
    if (!svgElement) return;
  
    const container = svgElement.parentElement;
    if (!container) return;
  
    const { width: containerWidth, height: containerHeight } = container.getBoundingClientRect();
    const margin = { top: 10, right: 10, bottom: 30, left: 10 }; // minimized margins
    const width = containerWidth;
    const height = containerHeight;
  
    const svg = d3.select(svgElement);
    svg.selectAll("*").remove(); // Clear previous chart
  
    const allTimes = Object.values(groupedBySim).flatMap((series) => series.map((d) => d.time));
    const xDomain = d3.extent(allTimes) as [number, number];
  
    const yDomain = [
      0,
      d3.max(Object.values(groupedBySim).flatMap((arr) => arr.map((d) => d.value))) || 100,
    ];
  
    const x = d3.scaleTime().domain(xDomain).range([margin.left, width - margin.right]);
    const y = d3.scaleLinear().domain(yDomain).range([height - margin.bottom, margin.top]);
  
    const xAxis = (g: any) =>
      g
        .attr("transform", `translate(0,${height - margin.bottom})`)
        .call(d3.axisBottom(x).tickFormat(d3.timeFormat("%H:%M")))
        .selectAll("text")
        .attr("font-size", "12px");
  
    svg.append("g").call(xAxis);
  
    Object.entries(groupedBySim).forEach(([sim, values], i) => {
      svg
        .append("path")
        .datum(values)
        .attr("fill", "none")
        .attr("stroke", "lightgrey")
        .attr("stroke-width", 1.5)
        .attr(
          "d",
          d3
            .line<{ time: number; value: number }>()
            .x((d) => x(d.time))
            .y((d) => y(d.value))
        )
        .on("mouseover", function (event, d) {
          d3.select(this).raise().attr("stroke", "steelblue");
          const [mouseX, mouseY] = d3.pointer(event, svgRef.current);
          const invertX = x.invert(mouseX);
          const closest = d.reduce((a, b) => {
            return Math.abs(a.time - invertX) < Math.abs(b.time - invertX) ? a : b;
          });
  
          setTooltipData({
            x: mouseX,
            y: mouseY,
            sim: sim,
            value: formatDollarValue(selectedColumn, closest.value),
            time: closest.time.toFixed(2),
          });
          setTooltipVisible(true);
        })
        .on("mousemove", function (event) {
          const [mouseX, mouseY] = d3.pointer(event, svgRef.current);
          setTooltipData((prev) => ({
            ...prev,
            x: mouseX,
            y: mouseY,
          }));
        })
        .on("mouseout", function () {
          d3.select(this).attr("stroke", "lightgrey");
          setTooltipVisible(false);
        });
    });
  };
  

  return (
    <Box sx={{ p: 2, width: "100%", flexWrap: "wrap" }}>
      {!loading && !error && (!data || !Array.isArray(data) || data.length === 0) ? (
        <Typography sx={{ textAlign: "center", minHeight: "200px", fontSize: "18px", marginTop:"5em" }}>No scenario data available for this use case.</Typography>
    ) : (
      <>
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-around",
          width: "100%",
        }}
      >
        <FormControl
          fullWidth
          size="small"
          variant="outlined"
          sx={{
            maxWidth: 250,
            marginRight: "30px",
          }}
        >
          <InputLabel
            id="column-select-label"
            style={{
              // fontSize:"1em",
              fontSize: '16px', fontWeight: 500, color:'#213547',
        fontFamily: 'Inter,system-ui, Avenir, Helvetica,Arial, sans-serif',
            }}
          >
            Column
          </InputLabel>
          <Select
            labelId="column-select-label"
            value={selectedColumn}
            onChange={(e) => setSelectedColumn(e.target.value)}
            label="Column"
            sx={{
              // fontSize: "0.85rem", // <-- controls selected value font size
              fontSize: '16px', fontWeight: 500, color:'#213547',
        fontFamily: 'Inter,system-ui, Avenir, Helvetica,Arial, sans-serif',
            }}
          >
            {numericColumns.map((col) => (
              <MenuItem key={col} value={col}>
                {col}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        {/* </Box> */}

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

      <Box sx={{ width: '100%', overflow: 'hidden' }}>
      <Box sx={{ width: '100%', height: '300px', position: 'relative' }}>
        <svg
          ref={svgRef}
          style={{ width: "100%", height: "100%", display: "block" }}
        />
        {tooltipVisible && (
          <div
            ref={tooltipRef}
            style={{
              position: "absolute",
              left: `${
                tooltipRef.current
                  ? Math.min(
                      tooltipData.x + 10,
                      window.innerWidth - tooltipRef.current.offsetWidth - 10
                    )
                  : tooltipData.x + 10
              }px`,
              top: `${tooltipData.y + 10}px`,
              background: "#fff",
              border: "1px solid #ccc",
              padding: "8px 14px",
              borderRadius: "6px",
              boxShadow: "0 4px 10px rgba(0,0,0,0.2)",
              pointerEvents: "none",
              fontSize: "14px",
              zIndex: 9999,
              minWidth: "120px",
              whiteSpace: "nowrap",
              textAlign: "left",
              maxWidth: "300px",
              color: "#000",
              colorScheme: "light",
            }}
          >
            <strong style={{ color: "#000" }}>Scenario:</strong> {tooltipData.sim}
            <br />
            <strong style={{ color: "#000" }}>Time:</strong> {tooltipData.time}
            <br />
            <strong style={{ color: "#000" }}>{selectedColumn}:</strong> {tooltipData.value}
          </div>
        )}

        <div
          ref={tooltipRef}
          style={{
            position: "absolute",
            padding: "8px 12px",
            background: "#fff",
            border: "1px solid #ccc",
            borderRadius: "4px",
            pointerEvents: "none",
            opacity: 0,
            boxShadow: "0 2px 6px rgba(0,0,0,0.2)",
            fontSize: "12px",
            zIndex: 9999,
            minWidth: "120px",
            whiteSpace: "nowrap",
          }}
        />
      </Box>
      </Box>
      {loading && !data.length && <Typography>Loading LMP data...</Typography>}

      {error && <Typography color="error">{error}</Typography>}
     </>
      )}
    </Box>
  )};
export default LMPPlot;
