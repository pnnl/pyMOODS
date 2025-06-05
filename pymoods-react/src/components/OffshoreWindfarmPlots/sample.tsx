import React, { useState, useEffect } from "react";
import RadarChart from "./RadarChart";
import * as d3 from "d3";

// Import centralized config
import config from '../../config';
const { API_BASE_URL } = config;

const DualRadarChart = ({ useCase, filters, topSolution }) => {
  const [loading, setLoading] = useState(true);
  const [objectives, setObjectives] = useState([]);
  const [decisions, setDecisions] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const params = new URLSearchParams();
        params.set("use_case", useCase);

        // Append filters
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

        // Normalize data for radar chart
        const normalize = (arr) =>
          arr.map((d) => {
            const max = d3.max(d.distribution || []);
            const normalizedDist = (d.distribution || []).map((v) => v / (max || 1));
            return {
              ...d,
              distribution: normalizedDist,
              max: max || 1,
              selected: (d.selected || 0) / (max || 1),
            };
          });

        setObjectives(normalize(result?.objectives || []));
        setDecisions(normalize(result?.decisions || []));
        setLoading(false);
      } catch (err) {
        console.error("Failed to fetch dual radar data:", err);
        setLoading(false);
      }
    };

    fetchData();
  }, [useCase, filters]);

  if (loading) return <div>Loading...</div>;

  return (
    <div style={{
      display: 'flex',
      gap: '20px',
      flexWrap: 'wrap',
      width: '100%',
      justifyContent: 'center'
    }}>
      {/* Left Chart - Objective Functions */}
      <div style={{ flex: '1 1 45%', minWidth: '250px' }}>
        <div style={{
          position: 'relative',
          width: '100%',
          paddingTop: '100%', // 1:1 aspect ratio
        }}>
          <div style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
          }}>
            <RadarChart
              key="objectives"
              data={objectives}
              title="Objective Functions"
              useCase={useCase}
              filters={filters}
              solution={topSolution?.objectives} // Pass top solution values
            />
          </div>
        </div>
      </div>

      {/* Right Chart - Decision Variables */}
      <div style={{ flex: '1 1 45%', minWidth: '250px' }}>
        <div style={{
          position: 'relative',
          width: '100%',
          paddingTop: '100%', // 1:1 aspect ratio
        }}>
          <div style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
          }}>
            <RadarChart
              key="decisions"
              data={decisions}
              title="Decision Variables"
              useCase={useCase}
              filters={filters}
              solution={topSolution?.decisions} // Pass top solution values
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default DualRadarChart;