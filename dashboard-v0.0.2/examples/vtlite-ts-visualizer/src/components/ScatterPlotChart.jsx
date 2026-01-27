// components/ScatterPlotChart.jsx
import React from 'react';
import {
  ScatterChart,
  XAxis,
  YAxis,
  ZAxis,
  Tooltip,
  Scatter,
  CartesianGrid,
  ResponsiveContainer
} from 'recharts';

const ScatterPlotChart = ({ data }) => {
  // Extract all numeric fields (excluding sim/time if needed)
  const numericFields = Object.keys(data[0]).filter(
    key =>
      typeof data[0][key] === 'number' &&
      !isNaN(data[0][key]) &&
      key !== 'sim' &&
      key !== 'time'
  );

  const [xAxis, setXAxis] = React.useState(numericFields[0]);
  const [yAxis, setYAxis] = React.useState(numericFields[1]);

  const formattedData = data.map(d => ({
    x: d[xAxis],
    y: d[yAxis]
  }));

  return (
    <div style={{ width: '100%', maxWidth: '900px', height: '500px', margin: '20px auto' }}>
      <h2>Interactive Scatter Plot</h2>
      <div style={{ marginBottom: '10px' }}>
        <label>
          X-axis:
          <select value={xAxis} onChange={(e) => setXAxis(e.target.value)}>
            {numericFields.map((field) => (
              <option key={field} value={field}>
                {field}
              </option>
            ))}
          </select>
        </label>
        <label style={{ marginLeft: '20px' }}>
          Y-axis:
          <select value={yAxis} onChange={(e) => setYAxis(e.target.value)}>
            {numericFields.map((field) => (
              <option key={field} value={field}>
                {field}
              </option>
            ))}
          </select>
        </label>
      </div>

      <ResponsiveContainer width="100%" height={400}>
        <ScatterChart>
          <CartesianGrid />
          <XAxis type="number" dataKey="x" name={xAxis} />
          <YAxis type="number" dataKey="y" name={yAxis} />
          <Tooltip cursor={{ strokeDasharray: '3 3' }} />
          <Scatter name={`${xAxis} vs ${yAxis}`} data={formattedData} fill="#8884d8" />
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
};

export default ScatterPlotChart;