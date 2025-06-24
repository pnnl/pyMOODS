import React, { useRef, useState, useEffect } from "react";
import * as d3 from "d3";

const BeeswarmPlot = ({ data, title = "Beeswarm Plot", isDecision = false }) => {
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
  const margin = { top: 0, right: 10, bottom: 100, left: 50 };

  useEffect(() => {
    if (!data || data.length === 0) return;

    const svg = d3.select(svgRef.current)
      .attr("width", "100%")
      .attr("height", "100%")
      .style("font", "12px sans-serif");

    svg.selectAll("*").remove(); // Clear previous content

    // Normalize each category's distribution to [0, 1]
    const normalizedData = data.map(d => {
        const values = d.distribution;
        const min = Math.min(...values);
        const max = Math.max(...values);
        const range = max - min;
    
        const normalizedValues = range === 0
        ? values.map(() => 0.5) // Handle constant data
        : values.map(v => (v - min) / range);
    
        return {
        ...d,
        distribution: normalizedValues,
        domain: [min, max],
        };
    });
    console.log("Data:", data)
    console.log("Normalized Data:", normalizedData)

    // const minValue = Math.min(...normalizedData.flatMap(d => d.distribution));
    // const maxValue = Math.max(...normalizedData.flatMap(d => d.distribution));

    // Responsive width and computed height
    const width = containerWidth;
    const categoryCount = normalizedData.length;
    const height = Math.max(300, categoryCount * 80); // ~80px per row, min 300px

    // Update scale ranges
    const xScale = d3.scaleLinear()
    .domain([0, 1])
    .range([margin.left+20, width - margin.right]);

    const yScale = d3.scaleBand()
    .domain(normalizedData.map((d, i) => i))
    .range([margin.top, height - margin.bottom])
    .padding(0.3);
    
    // // X scale: numeric values -> horizontal
    // const xScale = d3.scaleLinear()
    //   .domain([0, 1]).nice()
    //   .range([margin.left, width - margin.right]);

    // // Y scale: categories -> vertical
    // const yScale = d3.scaleBand()
    //   .domain(normalizedData.map((d, i) => i))
    //   .range([margin.top, height - margin.bottom])
    //   .padding(0.3);

    // Compute center Y of each category band
    const yCenter = (i) => yScale(i) + yScale.bandwidth() / 2;

    

    // --- Kernel Density Estimation Helper ---
    function kde(kernel) {
        return (samples) => (x) =>
        samples.reduce((sum, v) => sum + kernel(x - v), 0) / samples.length;
    }
    
    function epanechnikov(bandwidth) {
        return (x) => {
        x = Math.abs(x) / bandwidth;
        if (x >= 1) return 0;
        return (3 / (4 * bandwidth)) * (1 - x * x);
        };
    }
    
    // --- Draw Violin Paths ---
    const bandwidth = 0.2;
    
    // Draw violin plots using normalized distribution
    normalizedData.forEach((d, i) => {
        const values = d.distribution; // Use normalized values
        if (!values.length) return;
    
        const y = yCenter(i);
    
        // Kernel density estimation
        const kernel = epanechnikov(bandwidth);
        const density = kde(kernel)(values);
    
        // Generate points across normalized domain [0, 1]
        const numPoints = 50;
        const xs = d3.range(0, 1.02, 1 / numPoints); // From 0 to 1
        const densities = xs.map(x => density(x));
    
        // Scale density height (relative to category band)
        const maxDensity = Math.max(...densities);
        const scaleY = d3.scaleLinear()
        .domain([0, maxDensity])
        .range([0, yScale.bandwidth() / 2]);
    
        // Build upper half of violin (above center line)
        const upper = xs.map(xVal => {
        const xPos = xScale(xVal); // xScale is from 0 to 1
        const h = scaleY(density(xVal));
        return [xPos, y - h];
        });
    
        // Mirror it to build the lower half (below center line)
        const lower = [...xs].reverse().map(xVal => {
        const xPos = xScale(xVal);
        const h = scaleY(density(xVal));
        return [xPos, y + h];
        });
    
        // Combine into full shape
        const pathData = [...upper, ...lower];
    
        // Draw path
        svg.append("path")
        .attr("d", d3.line()
            .x(d => d[0])
            .y(d => d[1])(pathData))
        .attr("fill", "steelblue")
        .attr("opacity", 0.2)
        .attr("stroke", "none");
    });
    
    // Flatten all points for simulation
    const points = normalizedData.flatMap((d, catIndex) =>
      d.distribution.map(value => ({
        category: catIndex,
        value,
        radius: 5,
        color: isDecision ? "#4a4" : "steelblue"
      }))
    );

    // Force simulation
    const simulation = d3.forceSimulation(points)
      .force("x", d3.forceX(d => xScale(d.value)).strength(1))
      .force("y", d3.forceY(d => yCenter(d.category)).strength(1))
      .force("collision", d3.forceCollide().radius(d => d.radius + 1))
      .stop();

    for (let i = 0; i < 120; ++i) simulation.tick(); // Run ticks manually

    // Draw reference lines
    normalizedData.forEach((d, i) => {
    const y = yScale(i) + yScale.bandwidth() / 2;
    svg.append("line")
        .attr("x1", margin.left)
        .attr("x2", width - margin.right)
        .attr("y1", y)
        .attr("y2", y)
        .attr("stroke", "#ccc")
        .attr("stroke-dasharray", "4,2")
        .attr("opacity", 0.8);
    });

    // Draw beeswarm circles
    svg.selectAll("circle.point")
      .data(points)
      .enter()
      .append("circle")
      .attr("cx", d => d.x)
      .attr("cy", d => d.y)
      .attr("r", d => d.radius)
      .attr("fill", d => d.color)
      .attr("opacity", 0.6);

    // Highlight selected values
    normalizedData.forEach((d, i) => {
        const min = d.min;
        const max = d.max;
        const range = max - min;
        const selectedNormalized = range === 0
            ? 0.5
            : (d.selected - min) / range;
        
        const cy = yCenter(i);
        const cx = xScale(selectedNormalized);
      
      svg.append("circle")
        .attr("cx", cx)
        .attr("cy", cy)
        .attr("r", 8)
        .attr("fill", isDecision ? "#4a4" : "red")
        .attr("stroke", "black")
        .on("mouseover", function () {
          tooltip.style("display", null);
        })
        .on("mouseout", function () {
          tooltip.style("display", "none");
        })
        .on("mousemove", function (event) {
          tooltip
            .style("left", event.pageX + 10 + "px")
            .style("top", event.pageY - 20 + "px")
            .html(`${d.name}: ${d.selected.toFixed(1)}`);
        });
    });

    // Tooltip
    const tooltip = d3.select("body").append("div")
      .attr("class", "tooltip")
      .style("position", "absolute")
      .style("background", "#fff")
      .style("border", "1px solid #ccc")
      .style("padding", "6px 12px")
      .style("border-radius", "4px")
      .style("pointer-events", "none")
      .style("display", "none");

    // Add Y-axis (categories)
    const yAxis = d3.axisLeft(yScale).tickFormat(i => getAcronym(data[i].name));
    svg.append("g")
      .attr("transform", `translate(${margin.left},0)`)
      .call(yAxis)
      .selectAll("text")
      .style("text-anchor", "end")
      .attr("dy", ".35em")
      .style("font-size", "16px");

    // // Add X-axis (values)
    // svg.append("g")
    //   .attr("transform", `translate(0,${height - margin.bottom})`)
    //   .call(d3.axisBottom(xScale));

    return () => {
      tooltip.remove();
    };
  }, [data, isDecision]);

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
        fontWeight: "500",
        fontFamily:"Inter, system-ui, Avenir, Helvetica, Arial, sans-serif",
        fontSize: '15px',
        color: '#213547',
        }}>
        {title}
        </p>
      <svg
        ref={svgRef}
        width="100%"
        height="100%"
        viewBox={`0 0 ${size} ${size}`}
        preserveAspectRatio="xMidYMid meet"
      ></svg>
    </div>
  );
};

// Helper function
const getAcronym = (text) => {
  const cleaned = text.replace(/\([^)]*\)/g, '').trim();
  return cleaned
    .split(/[\s\-_]+/)
    .map(word => word[0]?.toUpperCase())
    .join('');
};

export default BeeswarmPlot;