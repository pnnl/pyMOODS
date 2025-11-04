import React, { useState, useEffect, useRef } from "react";
import * as d3 from "d3";

// Import centralized config
import config from '../../config';
const { API_BASE_URL } = config;

// Helper to generate acronyms like "Quality" → "QLT"
const getAcronym = (text) => {
  // Remove everything inside and including parentheses
  const cleaned = text.replace(/$.*?$/g, '').trim();

  return cleaned
    .split(/[\s\-_]+/)
    .map((word) => word.replace(/[^a-zA-Z0-9]/g, '').charAt(0).toUpperCase())
    .join("");
};

// Helper to position labels dynamically by quadrant
const getLabelPosition = (angleRad, baseX, baseY, offset = radius + 30) => {
  const x = baseX + offset * Math.cos(angleRad);
  const y = baseY + offset * Math.sin(angleRad);

  // Convert angle from radians to degrees for rotation
  let angleDeg = (angleRad * 180) / Math.PI;

  // Normalize angle to -90° to 270° for better text alignment
  if (angleDeg > 90 && angleDeg <= 270) {
    angleDeg -= 180; // Flip text for readability on left side
    return { x, y, transform: `rotate(${angleDeg} ${x} ${y})`, textAnchor: "end" };
  } else {
    return { x, y, transform: `rotate(${angleDeg} ${x} ${y})`, textAnchor: "start" };
  }
};

const ObjectivePlot = ({ useCase, filters = {} }) => {
  const [normalizedData, setNormalizedData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedValues, setSelectedValues] = useState([]);
  const [hoveredIndex, setHoveredIndex] = useState(null); // Track hovered axis index

  const svgRef = useRef();
  const containerRef = useRef(null);
  const [containerWidth, setContainerWidth] = useState(400); // Fallback width

  // Observe container size for responsiveness
  useEffect(() => {
    const updateSize = () => {
      if (containerRef.current) {
        setContainerWidth(containerRef.current.offsetWidth);
      }
    };

    updateSize();

    const resizeObserver = new ResizeObserver(updateSize);
    if (containerRef.current) {
      resizeObserver.observe(containerRef.current);
    }

    return () => {
      if (containerRef.current) {
        resizeObserver.unobserve(containerRef.current);
      }
    };
  }, []);

  const size = Math.min(containerWidth, 500); // Max width cap
  const radius = size / 2 - 60;
  const center = size / 2;
  const rotation = 30;

  const angleSlice = normalizedData.length > 0 ? (2 * Math.PI) / normalizedData.length : 0;
  const rotationRad = (rotation * Math.PI) / 180;

  const radialCoords = (r, angle) => [
    center + r * Math.cos(angle + rotationRad - Math.PI / 2),
    center + r * Math.sin(angle + rotationRad - Math.PI / 2),
  ];

  const findNearest = (val, distribution) => {
    if (!distribution.length) return val;
    return distribution.reduce((prev, curr) =>
      Math.abs(curr - val) < Math.abs(prev - val) ? curr : prev
    );
  };

  const handlePointerMove = (e, index) => {
    const svgRect = svgRef.current.getBoundingClientRect();
    const clientX = e.clientX - svgRect.left;
    const clientY = e.clientY - svgRect.top;
    const dx = clientX - center;
    const dy = clientY - center;
    const angle = index * angleSlice;

    const direction = [
      Math.cos(angle + rotationRad - Math.PI / 2),
      Math.sin(angle + rotationRad - Math.PI / 2),
    ];

    const projection = (dx * direction[0] + dy * direction[1]) / radius;
    const clamped = Math.max(0, Math.min(1, projection));
    const nearest = findNearest(clamped, normalizedData[index]?.distribution || []);

    setSelectedValues((prev) => {
      const updated = [...prev];
      updated[index] = nearest;
      return updated;
    });
  };

  const handlePointerDown = (index) => {
    const moveHandler = (e) => handlePointerMove(e, index);
    const upHandler = () => {
      window.removeEventListener("pointermove", moveHandler);
      window.removeEventListener("pointerup", upHandler);
    };

    window.addEventListener("pointermove", moveHandler);
    window.addEventListener("pointerup", upHandler);
  };

  useEffect(() => {
    const fetchData = async () => {
      try {
        const params = new URLSearchParams();
        params.set("use_case", useCase);

        Object.entries(filters).forEach(([key, value]) => {
          if (value && value.length > 0) {
            if (Array.isArray(value)) {
              value.forEach(v => params.append(key, v));
            } else {
              params.append(key, value);
            }
          }
        });

        const response = await fetch(`${API_BASE_URL}/api/objective-plot-data?${params.toString()}`);
        if (!response.ok) throw new Error("Network response was not ok");
        const result = await response.json();

        const normalized = result.map((d) => {
          const max = d3.max(d.distribution);
          const normalizedDist = d.distribution.map((v) => v / max);
          return {
            ...d,
            distribution: normalizedDist,
            max: max || 1,
            selected: (d.selected || 0) / (max || 1),
          };
        });

        setNormalizedData(normalized);
        setSelectedValues(normalized.map((d) => d.selected));
        setLoading(false);
      } catch (err) {
        console.error("Failed to fetch objective plot data:", err);
        setLoading(false);
      }
    };

    fetchData();
  }, [useCase, filters]);

  if (loading) {
    return (
      <div ref={containerRef} style={{ padding: "1rem", width: "100%" }}>
        Loading data...
      </div>
    );
  }

  if (!normalizedData.length) {
    return (
      <div ref={containerRef} style={{ padding: "1rem", width: "100%" }}>
        No data available
      </div>
    );
  }

  return (
    <div ref={containerRef} style={{ position: "relative", width: "100%", maxWidth: size, aspectRatio: "1/1" }}>
      <svg
        ref={svgRef}
        width="100%"
        height="100%"
        viewBox={`0 0 ${size} ${size}`}
        preserveAspectRatio="xMidYMid meet"
      >
        {/* Circular background */}
        <circle cx={center} cy={center} r={radius} fill="#f9f9f9" stroke="#888" strokeWidth={2} strokeDasharray="4 4" />

        {/* Axis lines + Dynamic Acronym Labels */}
        {normalizedData.map((d, i) => {
          const angleRad = i * angleSlice + rotationRad - Math.PI / 2;
          const { x: labelX, y: labelY, textAnchor, transform } = getLabelPosition(
            angleRad,
            center,
            center,
            radius + 30
          );
          const [axisX, axisY] = radialCoords(radius, i * angleSlice);

          return (
            <g key={`axis-${i}`}>
              {/* Axis Line */}
              <line x1={center} y1={center} x2={axisX} y2={axisY} stroke="#bbb" strokeWidth={1.5} />

              {/* Rotated Axis Label */}
              <text
                x={labelX}
                y={labelY}
                textAnchor={textAnchor}
                dominantBaseline="middle"
                fontSize={16}
                fontWeight="bold"
                fill="#333"
                transform={transform}
              >
                {getAcronym(d.variable)}
              </text>
            </g>
          );
        })}

        {/* Data dots */}
        {normalizedData.map((d, i) => {
          const angle = i * angleSlice;
          return d.distribution.map((val, j) => {
            const r = val * radius;
            const [x, y] = radialCoords(r, angle);
            return (
              <circle
                key={`dot-${i}-${j}`}
                cx={x}
                cy={y}
                r={5}
                fill="steelblue"
                opacity={0.4}
              />
            );
          });
        })}

        {/* Selected values with interaction */}
        {normalizedData.map((d, i) => {
          const angle = i * angleSlice;
          const r = selectedValues[i] * radius;
          const [x, y] = radialCoords(r, angle);
          const valueText = (selectedValues[i] * d.max).toFixed(1);

          const svgRect = svgRef.current?.getBoundingClientRect();
        const tooltipWidth = 200;
          const tooltipX = x + 10; // offset from red dot
          const tooltipY = y - 15;

          return (
            <g
              key={`selected-${i}`}
              onMouseOver={() => setHoveredIndex(i)}
              onMouseOut={() => setHoveredIndex(null)}
            >
              <circle
                cx={x}
                cy={y}
                r={10}
                fill="red"
                stroke="black"
                cursor="pointer"
                onPointerDown={() => handlePointerDown(i)}
                style={{ transition: "transform 0.2s ease" }}
              />

              {/* Tooltip Box */}
              {hoveredIndex === i && (
                <foreignObject
                  x={tooltipX}
                  y={tooltipY}
                  width={300}
                  height={60}
                  pointerEvents="none"
                >
                  <div
                    style={{
                      backgroundColor: "#fff",
                      border: "1px solid #ccc",
                      borderRadius: "6px",
                      padding: "8px 12px",
                      boxShadow: "0 2px 6px rgba(0,0,0,0.15)",
                      fontSize: "13px",           // Base font size
                      fontFamily: "sans-serif",
                      whiteSpace: "normal",       // Allow wrapping
                      wordWrap: "break-word",     // Break long words
                      overflowWrap: "break-word", // Better compatibility
                      maxWidth: "200px",          // Max width based on available space
                      maxHeight: "80px",          // Limit height
                      overflowY: "auto",          // Scroll if needed
                      boxSizing: "border-box",
                      hyphens: "auto",            // Optional: break words more elegantly
                      display: "inline-block",
                      textAlign: "left",          // Readable alignment
                      lineHeight: "1.3em",        // Compact lines
                    }}
                  >
                    {d.variable}: {valueText}
                  </div>
                </foreignObject>
              )}
            </g>
          );
        })}
      </svg>
    </div>
  );
};

export default ObjectivePlot;