import React, { useEffect, useState } from 'react';
import {
  ScatterChart, XAxis, YAxis, ZAxis, Tooltip, Scatter,
  ResponsiveContainer, CartesianGrid, Legend, Customized, Layer
} from 'recharts';
import { parse } from 'papaparse';

type DataRow = Record<string, number | string>;

const COLORS = [
  '#8884d8', '#82ca9d', '#ffc658', '#ff7300',
  '#d0ed57', '#8dd1e1', '#a4de6c', '#d88884', '#a28dd1'
];

const App: React.FC = () => {
  const [data, setData] = useState<DataRow[]>([]);
  const [numericFields, setNumericFields] = useState<string[]>([]);
  const [stringFields, setStringFields] = useState<string[]>([]);
  const [xAxisKey, setXAxisKey] = useState<string>('x_coord');
  const [yAxisKey, setYAxisKey] = useState<string>('y_coord');
  const [colorByKey, setColorByKey] = useState<string>('label');
  const [uniqueCategories, setUniqueCategories] = useState<string[]>([]);

  const [zAxisKey] = useState<string>('Weighted Sum');

  useEffect(() => {
    fetch('/scenarios.csv')
      .then(response => response.text())
      .then(csvData => {
        const result = parse(csvData, {
          header: true,
          dynamicTyping: true,
          skipEmptyLines: true,
        });

        const parsedData = result.data as DataRow[];
        setData(parsedData);

        if (parsedData.length > 0) {
          const firstRow = parsedData[0];

          const numeric = Object.keys(firstRow).filter(
            key => typeof firstRow[key] === 'number' && !isNaN(firstRow[key] as number)
          );

          const strings = Object.keys(firstRow).filter(
            key => typeof firstRow[key] === 'string'
          );

          setNumericFields(numeric);
          setStringFields(strings);

          if (strings.includes('label')) {
            setColorByKey('label');
          } else if (strings.length > 0) {
            setColorByKey(strings[0]);
          }
        }
      });
  }, []);

  useEffect(() => {
    if (colorByKey && data.length > 0) {
      const categories = Array.from(new Set(data.map(row => row[colorByKey] as string)));
      setUniqueCategories(categories);
    }
  }, [colorByKey, data]);

  const colorMap = uniqueCategories.reduce<Record<string, string>>((acc, cat, idx) => {
    acc[cat] = COLORS[idx % COLORS.length];
    return acc;
  }, {});

  const formattedData = data.map(row => ({
    ...row,
    x: row[xAxisKey],
    y: row[yAxisKey],
    z: row[zAxisKey],
    color: colorMap[row[colorByKey] as string] || '#ccc'
  }));

  const renderBoundary = ({ xAxis, yAxis }: any) => {
    // These are the chart's inner bounds
    const x0 = xAxis[0].scale.range()[0];
    const x1 = xAxis[0].scale.range()[1];
    const y0 = yAxis[0].scale.range()[0];
    const y1 = yAxis[0].scale.range()[1];
  
    return (
      <rect
        x={Math.min(x0, x1)}
        y={Math.min(y0, y1)}
        width={Math.abs(x1 - x0)}
        height={Math.abs(y1 - y0)}
        fill="none"
        stroke="#ccc"
        strokeWidth={2}
      />
    );
  };  

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h1>Interactive Scatter Plot</h1>

      <div style={{ marginBottom: '20px', display: 'flex', gap: '20px', flexWrap: 'wrap' }}>
        <label>
          X-axis:
          <select value={xAxisKey} onChange={(e) => setXAxisKey(e.target.value)}>
            {numericFields.map((field) => (
              <option key={field} value={field}>
                {field}
              </option>
            ))}
          </select>
        </label>

        <label>
          Y-axis:
          <select value={yAxisKey} onChange={(e) => setYAxisKey(e.target.value)}>
            {numericFields.map((field) => (
              <option key={field} value={field}>
                {field}
              </option>
            ))}
          </select>
        </label>

        <label>
          Color by:
          <select value={colorByKey} onChange={(e) => setColorByKey(e.target.value)}>
            {stringFields.map((field) => (
              <option key={field} value={field}>
                {field}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div style={{ width: '100%', height: 500 }}>
      <ResponsiveContainer>
        <ScatterChart margin={{ top: 20, right: 20, bottom: 50, left: 20 }}>
          <CartesianGrid horizontal={false} vertical={false} />
          <XAxis type="number" dataKey="x" />
          <YAxis type="number" dataKey="y" />
          <ZAxis type="number" dataKey="z" range={[20, 100]} />
          <Tooltip />
          <Legend verticalAlign="bottom" wrapperStyle={{ paddingTop: 10, display: 'flex', flexWrap: 'wrap', gap: '10px' }} />

          {uniqueCategories.map((cat) => (
            <Scatter
              key={cat}
              name={cat}
              data={formattedData.filter(row => row[colorByKey] === cat)}
              fill={colorMap[cat]}
            />
          ))}

          <Customized component={({ xAxisMap, yAxisMap }) => {
            const x = xAxisMap[0].scale.range()[0];
            const xMax = xAxisMap[0].scale.range()[1];
            const y = yAxisMap[0].scale.range()[0];
            const yMax = yAxisMap[0].scale.range()[1];
            return (
              <Layer>
                <rect
                  x={Math.min(x, xMax)}
                  y={Math.min(y, yMax)}
                  width={Math.abs(xMax - x)}
                  height={Math.abs(yMax - y)}
                  fill="none"
                  stroke="#ccc"
                  strokeWidth={2}
                />
              </Layer>
            );
          }} />
        </ScatterChart>
      </ResponsiveContainer>
      </div>
    </div>
  );
};

export default App;
