import React, { useState, useRef } from "react";
import * as d3 from "d3";

const RadialDistributionChart = ({ data, size = 500, rotation = 30 }) => {
  const radius = size / 2 - 60;
  const center = size / 2;
  const angleSlice = (2 * Math.PI) / data.length;
  const rotationRad = (rotation * Math.PI) / 180;

  // Normalize data and compute scale
  const normalizedData = data.map((d) => {
    const max = d3.max(d.distribution);
    const normalized = d.distribution.map((v) => v / max);
    return {
      ...d,
      distribution: normalized,
      max: max,
      selected: d.selected / max,
    };
  });

  const [selectedValues, setSelectedValues] = useState(
    normalizedData.map((d) => d.selected)
  );

  const svgRef = useRef();

  const radialCoords = (r, angle) => [
    center + r * Math.cos(angle + rotationRad - Math.PI / 2),
    center + r * Math.sin(angle + rotationRad - Math.PI / 2),
  ];

  const findNearest = (val, distribution) => {
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
    const nearest = findNearest(clamped, normalizedData[index].distribution);

    const updated = [...selectedValues];
    updated[index] = nearest;
    setSelectedValues(updated);
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
    <svg ref={svgRef} width={size} height={size} style={{ border: "1px solid #ddd" }}>
      <circle
        cx={center}
        cy={center}
        r={radius}
        fill="none"
        stroke="#aaa"
        strokeDasharray="4 4"
      />

      {normalizedData.map((d, i) => {
        const angle = i * angleSlice;
        const [x, y] = radialCoords(radius, angle);
        return (
          <g key={`axis-${i}`}>
            <line x1={center} y1={center} x2={x} y2={y} stroke="#aaa" />
            <text
              x={x}
              y={y}
              textAnchor="middle"
              dominantBaseline="central"
              fontSize={12}
              transform={`translate(${(x - center) * 0.1}, ${(y - center) * 0.1})`}
            >
              {d.variable}
            </text>
          </g>
        );
      })}

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
              opacity={0.8}
            />
          );
        });
      })}

      {normalizedData.map((d, i) => {
        const angle = i * angleSlice;
        const r = selectedValues[i] * radius;
        const [x, y] = radialCoords(r, angle);
        return (
          <g key={`selected-${i}`}>
            <circle
              cx={x}
              cy={y}
              r={8}
              fill="red"
              stroke="black"
              cursor="pointer"
              onPointerDown={() => handlePointerDown(i)}
              style={{ transition: "cx 0.2s, cy 0.2s" }}
            />
            <text
              x={x}
              y={y - 14}
              textAnchor="middle"
              fontSize={12}
              fill="#000"
            >
              {(selectedValues[i] * d.max).toFixed(1)}
            </text>
          </g>
        );
      })}
    </svg>
  );
};

export default RadialDistributionChart;
