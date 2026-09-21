import React, { useEffect, useState } from "react";
import NetworkGraph, { RawNode, RawLine } from "./NetworkGraph";
import { Typography, Box } from "@mui/material";
import config from "../../config";

const { API_BASE_URL } = config;

// Map filter values to file name segments
const LOCATION_MAP: Record<string, string> = {
  rural_tech_hub: "rural_tech_hub",
  industrial_park: "industrial_park",
  urban_edge: "urban_edge",
};

const OPERATION_MAP: Record<string, string> = {
  AIML_focused: "AIML_focused",
  standard: "standard",
  high_redundancy: "high_redundancy",
};

type NetworkGraphPanelProps = {
  filters: Record<string, string[]>;
};

const NetworkGraphPanel: React.FC<NetworkGraphPanelProps> = ({ filters }) => {
  const [nodes, setNodes] = useState<RawNode[] | null>(null);
  const [lines, setLines] = useState<RawLine[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Extract first selected value for each relevant filter
  const locationValues = filters["Location Scenario"] || [];
  const operationValues = filters["Operation Model"] || [];

  const location = locationValues.length > 0 ? locationValues[0] : null;
  const operation = operationValues.length > 0 ? operationValues[0] : null;

  const locationKey = location && LOCATION_MAP[location] ? LOCATION_MAP[location] : null;
  const operationKey = operation && OPERATION_MAP[operation] ? OPERATION_MAP[operation] : null;

  useEffect(() => {
    if (!locationKey || !operationKey) {
      setNodes(null);
      setLines(null);
      setError(null);
      return;
    }

    const nodeFile = `node_data_${locationKey}_${operationKey}.json`;
    const lineFile = `line_data_${locationKey}_${operationKey}.json`;

    const basePath = `${API_BASE_URL}/api/network-graph`;

    Promise.all([
      fetch(`${basePath}?file=${encodeURIComponent(nodeFile)}`).then((r) => {
        if (!r.ok) throw new Error(`Failed to load ${nodeFile}`);
        return r.json();
      }),
      fetch(`${basePath}?file=${encodeURIComponent(lineFile)}`).then((r) => {
        if (!r.ok) throw new Error(`Failed to load ${lineFile}`);
        return r.json();
      }),
    ])
      .then(([nodeData, lineData]) => {
        setNodes(nodeData);
        setLines(lineData);
        setError(null);
      })
      .catch((err) => {
        console.error("Error loading network graph data:", err);
        setError(err.message);
        setNodes(null);
        setLines(null);
      });
  }, [locationKey, operationKey]);

  if (!locationKey || !operationKey) {
    return (
      <Box sx={{ display: "flex", alignItems: "center", justifyContent: "center", width: "100%", height: "100%" }}>
        <Typography variant="body2" color="text.secondary">
          Select a Location Scenario and Operation Model to view the network graph.
        </Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%" }}>
        <Typography variant="body2" color="error">
          {error}
        </Typography>
      </Box>
    );
  }

  if (!nodes || !lines) {
    return (
      <Box sx={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%" }}>
        <Typography variant="body2" color="text.secondary">
          Loading network graph...
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ width: "100%", height: "100%", display: "flex", flexDirection: "column", minHeight: 0 }}>
      <NetworkGraph nodes={nodes} lines={lines} />
    </Box>
  );
};

export default NetworkGraphPanel;
