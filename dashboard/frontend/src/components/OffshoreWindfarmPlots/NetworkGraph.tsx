import React from "react";
import Plot from "react-plotly.js";
import { Data } from "plotly.js";

// Raw data (matches JSON)
export type RawNode = {
  node_id: number;
  name: string;
  type: string; // e.g. "transfer", "load", etc.
  voltage_level: number;
  base_load_mw: number;
  peak_load_mw: number;
  load_factor: number;
  congestion_factor: number;
  importance: number;
};

export type RawLine = {
  line_id: number;
  from_node: number;
  to_node: number;
  status: "existing" | "candidate" | string;
  r_pu: number;
  x_pu: number;
  capacity_mva: number;
  length_km: number;
  voltage_kv: number;
  contingency_factor: number;
  max_expansion_mva: number;
  is_datacenter_connection: boolean;
};

// Enriched runtime shape with layout coordinates
export type GraphNode = RawNode & {
  x: number;
  y: number;
};

export type GraphEdge = RawLine;

function layoutNodes(rawNodes: RawNode[], rawLines: RawLine[]): GraphNode[] {
  const n = rawNodes.length;
  if (n === 0) return [];

  // Initialize positions in a circle (starting point for force simulation)
  const radius = 10;
  const positions: { x: number; y: number }[] = rawNodes.map((_, index) => {
    const angle = (2 * Math.PI * index) / Math.max(n, 1);
    return { x: radius * Math.cos(angle), y: radius * Math.sin(angle) };
  });

  // Build adjacency from lines
  const nodeIdToIndex = new Map<number, number>(
    rawNodes.map((node, i) => [node.node_id, i])
  );
  const edges: [number, number][] = [];
  for (const line of rawLines) {
    const srcIdx = nodeIdToIndex.get(line.from_node);
    const dstIdx = nodeIdToIndex.get(line.to_node);
    if (srcIdx !== undefined && dstIdx !== undefined) {
      edges.push([srcIdx, dstIdx]);
    }
  }

  // Force-directed simulation (Fruchterman-Reingold)
  const area = 400;
  const k = Math.sqrt(area / Math.max(n, 1)); // ideal spring length
  const iterations = 200;
  let temperature = 10;
  const coolingFactor = temperature / iterations;

  for (let iter = 0; iter < iterations; iter++) {
    const disp: { x: number; y: number }[] = positions.map(() => ({ x: 0, y: 0 }));

    // Repulsive forces between all node pairs
    for (let i = 0; i < n; i++) {
      for (let j = i + 1; j < n; j++) {
        const dx = positions[i].x - positions[j].x;
        const dy = positions[i].y - positions[j].y;
        const dist = Math.max(Math.sqrt(dx * dx + dy * dy), 0.01);
        const force = (k * k) / dist;
        const fx = (dx / dist) * force;
        const fy = (dy / dist) * force;
        disp[i].x += fx;
        disp[i].y += fy;
        disp[j].x -= fx;
        disp[j].y -= fy;
      }
    }

    // Attractive forces along edges
    for (const [srcIdx, dstIdx] of edges) {
      const dx = positions[srcIdx].x - positions[dstIdx].x;
      const dy = positions[srcIdx].y - positions[dstIdx].y;
      const dist = Math.max(Math.sqrt(dx * dx + dy * dy), 0.01);
      const force = (dist * dist) / k;
      const fx = (dx / dist) * force;
      const fy = (dy / dist) * force;
      disp[srcIdx].x -= fx;
      disp[srcIdx].y -= fy;
      disp[dstIdx].x += fx;
      disp[dstIdx].y += fy;
    }

    // Apply displacement limited by temperature
    for (let i = 0; i < n; i++) {
      const dx = disp[i].x;
      const dy = disp[i].y;
      const dist = Math.max(Math.sqrt(dx * dx + dy * dy), 0.01);
      const limitedDist = Math.min(dist, temperature);
      positions[i].x += (dx / dist) * limitedDist;
      positions[i].y += (dy / dist) * limitedDist;
    }

    temperature -= coolingFactor;
  }

  return rawNodes.map((node, i) => ({
    ...node,
    x: positions[i].x,
    y: positions[i].y,
  }));
}

export function buildNetworkPlotData(
  rawNodes: RawNode[],
  rawLines: RawLine[]
): Data[] {
  const nodes: GraphNode[] = layoutNodes(rawNodes, rawLines);

  // Map node_id -> node with coords
  const nodeById = new Map<number, GraphNode>(
    nodes.map(n => [n.node_id, n])
  );

  // Build edge traces — separate traces for existing vs candidate lines
  const existingEdgeX: (number | null)[] = [];
  const existingEdgeY: (number | null)[] = [];
  const candidateEdgeX: (number | null)[] = [];
  const candidateEdgeY: (number | null)[] = [];

  for (const line of rawLines) {
    const src = nodeById.get(line.from_node);
    const dst = nodeById.get(line.to_node);
    if (!src || !dst) continue;

    if (line.status === "candidate") {
      candidateEdgeX.push(src.x, dst.x, null);
      candidateEdgeY.push(src.y, dst.y, null);
    } else {
      existingEdgeX.push(src.x, dst.x, null);
      existingEdgeY.push(src.y, dst.y, null);
    }
  }

  const existingEdgeTrace = {
    x: existingEdgeX,
    y: existingEdgeY,
    type: "scatter" as const,
    mode: "lines" as const,
    line: { width: 1.5, color: "#666666" },
    hoverinfo: "none" as const,
    name: "Existing lines",
  };

  const candidateEdgeTrace = {
    x: candidateEdgeX,
    y: candidateEdgeY,
    type: "scatter" as const,
    mode: "lines" as const,
    line: { width: 1.5, color: "#ff7f0e", dash: "dash" as const },
    hoverinfo: "none" as const,
    name: "Candidate lines",
  };

  const nodeTrace = {
    x: nodes.map(n => n.x),
    y: nodes.map(n => n.y),
    type: "scatter" as const,
    mode: "markers" as const,
    showlegend: false,
    text: nodes.map(n => n.name),
    customdata: nodes.map(n => [
      n.type,
      n.voltage_level,
      n.base_load_mw,
      n.peak_load_mw,
      n.importance,
    ]),
    hovertemplate:
      "<b>%{text}</b><br>" +
      "Type: %{customdata[0]}<br>" +
      "Voltage: %{customdata[1]} kV<br>" +
      "Base load: %{customdata[2]} MW<br>" +
      "Peak load: %{customdata[3]} MW<br>" +
      "Importance: %{customdata[4]}<extra></extra>",
    hoverlabel: {
      bgcolor: "white",
      font: { color: "black" },
      bordercolor: "#ccc",
    },
    marker: {
      size: nodes.map(n => 8 + n.importance * 12),
      color: nodes.map(n => n.voltage_level),
      colorscale: "Viridis",
      sizemode: "diameter" as const,
      showscale: true,
      colorbar: {
        title: { text: "Voltage (kV)" },
        x: 1.02,
        y: 0.5,
        len: 0.5,
      },
      line: {
        color: "#ffffff",
        width: 1,
      },
    },
  };

  return [existingEdgeTrace, candidateEdgeTrace, nodeTrace] as Data[];
}

type NetworkGraphProps = {
  nodes: RawNode[];
  lines: RawLine[];
  height?: number;
};

const NetworkGraph: React.FC<NetworkGraphProps> = ({
  nodes,
  lines,
  height = 600,
}) => {
  const data = React.useMemo(
    () => buildNetworkPlotData(nodes, lines),
    [nodes, lines]
  );

  const layout: Partial<Plotly.Layout> = {
    title: { text: "Transmission Network", y: 0.92 },
    showlegend: true,
    legend: {
      x: 0,
      y: 0,
      orientation: "h" as const,
    },
    hovermode: "closest",
    margin: { l: 20, r: 80, t: 40, b: 30 },
    xaxis: {
      visible: false,
      zeroline: false,
      showgrid: false,
    },
    yaxis: {
      visible: false,
      zeroline: false,
      showgrid: false,
      scaleanchor: "x",
      scaleratio: 1,
    },
  };

  const config: Partial<Plotly.Config> = {
    responsive: true,
    displaylogo: false,
  };

  return (
    <Plot
      data={data}
      layout={{ ...layout, autosize: true }}
      config={config}
      style={{ width: "100%", height: "100%" }}
      useResizeHandler
    />
  );
};

export default NetworkGraph;