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

// Define Solution type if not already defined elsewhere
export type Solution = Record<string, number | string>;

interface ScatterPlotProps {
    useCase: string;
    solutionsData: Solution[];
    onColorByChange?: (colorBy: string) => void;
  }
  
  const ScatterPlot: React.FC<ScatterPlotProps> = ({ 
    useCase,
    solutionsData,
    onColorByChange 
  }) => {

    // Ensure there's data before extracting fields
    const hasData = solutionsData.length > 0;
    
    // Extract numeric fields dynamically
  const numericFields = hasData
  ? Object.keys(solutionsData[0]).filter(key => {
      const value = solutionsData[0][key];
      return (
        typeof value === 'number' &&
        !isNaN(value) &&
        key !== 'sim' &&
        key !== 'time' &&
        key !== 'Solution ID' &&
        key !== 'Case Study' &&
        key !== 'Location'
      );
    })
  : [];

  const [xAxis, setXAxis] = React.useState(numericFields[0] || '');
  const [yAxis, setYAxis] = React.useState(numericFields[1] || '');

  const formattedData = solutionsData.map(datum => ({
    x: datum[xAxis],
    y: datum[yAxis]
  }));

  return (
    <div style={{ width: '100%', maxWidth: '900px', height: '100%', margin: '5px auto', padding: '0px' }}>
  {/* Stacked Form Controls */}
  <div style={{
    display: 'flex',
    justifyContent: 'space-between',
    gap: '10px',
    marginBottom: '10px',
    flexWrap: 'wrap'
  }}>
    <label style={{ display: 'flex', flexDirection: 'column', fontSize: '14px',
      minWidth: '200px',
      flex: 1,
      maxWidth: '250px' }}>
      X-axis:
      <select
        value={xAxis}
        onChange={(e) => setXAxis(e.target.value)}
        style={{ width: '100%', maxWidth: '250px', padding: '5px', marginTop: '4px',
          textAlign: 'center',
          textAlignLast: 'center' }}
      >
        {numericFields.map((field) => (
          <option key={field} value={field}>
            {field}
          </option>
        ))}
      </select>
    </label>

    <label style={{ display: 'flex', flexDirection: 'column', fontSize: '14px',
      minWidth: '200px',
      flex: 1,
      maxWidth: '250px' }}>
      Y-axis:
      <select
        value={yAxis}
        onChange={(e) => setYAxis(e.target.value)}
        style={{ width: '100%', maxWidth: '250px', padding: '5px', marginTop: '4px',
          textAlign: 'center',
          textAlignLast: 'center' }}
      >
        {numericFields.map((field) => (
          <option key={field} value={field}>
            {field}
          </option>
        ))}
      </select>
    </label>
  </div>

  {/* Scatter Chart with Adjustments */}
  <ResponsiveContainer width="100%" height={400}>
    <ScatterChart
      margin={{
        top: 20,
        right: 0,
        bottom: 20,
        left: 0 // Reduced left margin to remove white space
      }}
    >
      <CartesianGrid />
      <XAxis
        type="number"
        dataKey="x"
        name={xAxis}
        tick={{ visibility: 'hidden' }} 
        tickLine={{ visibility: 'hidden' }}
        axisLine={false}
      />
      <YAxis
        type="number"
        dataKey="y"
        name={yAxis}
        tick={{ visibility: 'hidden' }} 
        tickLine={{ visibility: 'hidden' }}
        axisLine={false}
        yAxisId={0}
        hide
      />
      <Tooltip cursor={{ strokeDasharray: '3 3' }} />
      <Scatter name={`${xAxis} vs ${yAxis}`} data={formattedData} fill="#8884d8" />
    </ScatterChart>
  </ResponsiveContainer>
</div>
  );
};

export default ScatterPlot;