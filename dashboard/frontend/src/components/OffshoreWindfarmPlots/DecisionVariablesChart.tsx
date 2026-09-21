import React from "react";
import { Box, CircularProgress } from "@mui/material";
import BeeswarmPlot from "./BeeSwarm";

// Define interface for decision data
export interface DecisionData {
  name: string;
  distribution: number[];
  selected: number;
  min?: number;
  max?: number;
}

interface DecisionVariablesChartProps {
  decisions: DecisionData[];
  loading: boolean;
}

const DecisionVariablesChart: React.FC<DecisionVariablesChartProps> = ({ decisions, loading }) => {
  if (loading) return (
    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
      <CircularProgress size={24} />
    </Box>
  );
  
  return (
    <BeeswarmPlot
      key="decisions"
      data={decisions}
      title=""
    />
  );
};

export default DecisionVariablesChart;