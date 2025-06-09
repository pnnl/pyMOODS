import React, { useState, useRef } from "react";
import * as d3 from "d3";

const getAcronym = (text: string): string => {
  // Remove all parenthetical expressions, like ($k)
  const cleaned = text.replace(/\([^)]*\)/g, '').trim();

  return cleaned
    .split(/[\s\-_]+/) // Split on space or hyphen
    .map((word) => word[0]?.toUpperCase())
    .join('');
};

// Label position helper by quadrant
const getLabelPosition = (angleRad, baseX, baseY, radius) => {
    // Place labels inside the radar circle
    const offset = radius * 0.8; // 80% of the radius inward
  
    const x = baseX + offset * Math.cos(angleRad);
    const y = baseY + offset * Math.sin(angleRad);
  
    let angleDeg = (angleRad * 180) / Math.PI;
  
    let textAnchor = "middle";
    let dominantBaseline = "central";
  
    // Flip text if it's on the left side for better readability
    if (angleDeg > 90 && angleDeg < 270) {
      angleDeg += 180;
      textAnchor = "middle";
    }
  
    return {
      x,
      y,
      textAnchor,
      dominantBaseline,
      transform: `rotate(${angleDeg} ${x} ${y})`,
    };
  };

const RadarChart = ({ data, title = "Radar Chart", isDecision = false }) => {
  const [selectedValues, setSelectedValues] = useState(data.map(d => d.selected || 0));
  const [hoveredIndex, setHoveredIndex] = useState(null);
  const svgRef = useRef();
  const containerRef = useRef(null);
  const [containerWidth, setContainerWidth] = useState(400);

  // Resize observer for responsiveness
  useState(() => {
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

  const size = containerWidth;
  const radius = size / 2;
  const center = size / 2;
  const rotation = 30;
  const angleSlice = data.length > 0 ? (2 * Math.PI) / data.length : 0;
  const rotationRad = (rotation * Math.PI) / 180;

  const radialCoords = (r, angle) =>
    [
      center + r * Math.cos(angle + rotationRad - Math.PI / 2),
      center + r * Math.sin(angle + rotationRad - Math.PI / 2)
    ];

  const findNearest = (val, distribution) => {
    if (!distribution?.length) return val;
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
      Math.sin(angle + rotationRad - Math.PI / 2)
    ];
    const projection = (dx * direction[0] + dy * direction[1]) / radius;
    const clamped = Math.max(0, Math.min(1, projection));
    const nearest = findNearest(clamped, data[index]?.distribution || []);
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

  return (
    <div
      ref={containerRef}
      style={{
        width: "100%",
        aspectRatio: "1/1",
        position: "relative",
        margin: 0,
        padding: 0,
      }}
    >
      <p style={{
        textAlign: 'center',
        marginBottom: '10px',
        fontWeight: "bold",
        fontSize: '14px',
        color: '#555',
        }}>
        {title}
        </p>
      <svg
        ref={svgRef}
        width="100%"
        height="100%"
        viewBox={`0 0 ${size} ${size}`}
        preserveAspectRatio="xMidYMid meet"
      >
        {/* White background */}
        <rect width="100%" height="100%" fill="white" />

        {/* Outer Circular Boundary */}
        <circle
            cx={center}
            cy={center}
            r={radius}
            fill="none"
            stroke="gray"
            strokeWidth={2}
        />

        {/* Axis lines + Acronym Labels */}
        {/* Axis lines + Dynamic Acronym Labels */}
        {data.map((d, i) => {
        const angleRad = i * angleSlice + rotationRad - Math.PI / 2;
        const { x: labelX, y: labelY, textAnchor, dy } = getLabelPosition(
            angleRad,
            center,
            center,
            radius
        );
        const [axisX, axisY] = radialCoords(radius, i * angleSlice);
        return (
            <g key={`axis-${i}`}>
            <line x1={center} y1={center} x2={axisX} y2={axisY} stroke="#bbb" strokeWidth={1.5} />
            <text
                x={labelX}
                y={labelY}
                textAnchor={textAnchor}
                dominantBaseline="central"
                fontSize={24}
                fontWeight="normal"
                fill="#333"
                dy={dy}
            >
                {getAcronym(d.name)}
            </text>
            </g>
        );
        })}

        {/* Data dots */}
        {
        data.map((d, i) => {
          const angle = i * angleSlice;
          return d.distribution.map((val, j) => {
            const normalizedVal = val / d.max;
            const r = normalizedVal * radius;
            const [x, y] = radialCoords(r, angle);
            return (
              <circle
                key={`dot-${i}-${j}`}
                cx={x}
                cy={y}
                r={5}
                fill={isDecision ? "#4a4" : "steelblue"}
                opacity={0.4}
              />
            );
          });
        })}

        {/* Selected point indicators */}
        {data.map((d, i) => {
          const angle = i * angleSlice;
          const normalizedVal = selectedValues[i] / d.max;
          const r = normalizedVal * radius;
          const [x, y] = radialCoords(r, angle);
          const valueText = (selectedValues[i]).toFixed(1);
          const tooltipX = x + 10;
          const tooltipY = y - 15;
          const tooltipWidth = 220;
          const tooltipHeight = 60;
          const padding = 10;

          let adjustedX = tooltipX;
          let adjustedY = tooltipY;

          // Clamp horizontally
          if (tooltipX + tooltipWidth > size) {
            adjustedX = size - tooltipWidth - padding;
          } else if (tooltipX < 0) {
            adjustedX = padding;
}

          // Clamp vertically
          if (tooltipY + tooltipHeight > size) {
            adjustedY = size - tooltipHeight - padding;
          } else if (tooltipY < 0) {
            adjustedY = padding;
}
          
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
                fill={isDecision ? "#4a4" : "red"}
                stroke="black"
                cursor="pointer"
                onPointerDown={() => handlePointerDown(i)}
                style={{ transition: "transform 0.2s ease" }}
              />
              {/* Tooltip Box */}
              {hoveredIndex === i && (
                <foreignObject
                  x={adjustedX}
                  y={adjustedY}
                  width={tooltipWidth}
                  height={tooltipHeight}
                  pointerEvents="none"
                >
                  <div
                    style={{
                      backgroundColor: "#fff",
                      border: "1px solid #ccc",
                      borderRadius: "6px",
                      padding: "8px 12px",
                      boxShadow: "0 2px 6px rgba(0,0,0,0.15)",
                      fontSize: "18px",
                      fontFamily: "sans-serif",
                      whiteSpace: "normal",
                      wordWrap: "break-word",
                      overflowWrap: "break-word",
                      maxWidth: "250px",
                      maxHeight: "80px",
                      overflowY: "auto",
                      boxSizing: "border-box",
                      hyphens: "auto",
                      display: "inline-block",
                      textAlign: "left",
                      lineHeight: "1.3em",
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

export default RadarChart;