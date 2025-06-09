import React from "react";
import RadarChart from "./RadarChart";

// Define interface for radar data
export interface RadarData {
  name: string;
  distribution: number[];
  selected: number;
  min?: number;
  max?: number;
}

interface DualRadarChartProps {
  objectives: RadarData[];
  decisions: RadarData[];
  loading: boolean;
}

const DualRadarChart: React.FC<DualRadarChartProps> = ({ objectives, decisions, loading }) => {
  if (loading) return <div>Loading...</div>;
  
  return (
    <div style={{
      display: 'flex',
      gap: '20px',
      flexWrap: 'wrap',
      width: '100%'
    }}>
      {/* Left Chart */}
      <div style={{
        flex: '1 1 45%',
        aspectRatio: '1/1'
      }}>
        <RadarChart
          key="objectives"
          data={objectives}
          title="Objective Functions"
        />
      </div>

      {/* Right Chart */}
      <div style={{
        flex: '1 1 45%',
        aspectRatio: '1/1'
      }}>
        <RadarChart
          key="decisions"
          data={decisions}
          title="Decision Variables"
        />
      </div>
    </div>
  );
};

export default DualRadarChart;