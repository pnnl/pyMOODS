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
  ResponsiveContainer,
  Legend,
  Dot,
  DotProps
} from 'recharts';

type CustomDotProps = DotProps & {
  fill?: string;
  isTooltipActive?: boolean;
};

// Define Solution type if not already defined elsewhere
export type Solution = Record<string, number | string>;

interface ScatterPlotProps {
  useCase: string;
  solutionsData: Solution[];
  decision_keys?: string[];   
  objective_keys?: string[];  
  onColorByChange?: (colorBy: string) => void;
  objectiveColorMap: Record<string, string>;
}

const COLORS = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96A6C5', '#FAC84D', '#FFA07A', '#8FBC8F'];
  
const ScatterPlot: React.FC<ScatterPlotProps> = ({ 
  useCase,
  solutionsData,
  decision_keys,
  objective_keys,
  onColorByChange,
  objectiveColorMap 
}) => {

  // Ensure there's data before extracting fields
  const hasData = solutionsData.length > 0;
  console.log(solutionsData)
  console.log(decision_keys)
  console.log(objective_keys)
  
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

  const [xAxis, setXAxis] = React.useState('x_coord');
  const [yAxis, setYAxis] = React.useState('y_coord');

  const labelField = "label";

  const formattedData = solutionsData.map(datum => ({
    ...datum,
    x: datum[xAxis],
    y: datum[yAxis]
  }));

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      console.log('Tooltip Payload:', payload); // Log the tooltip payload for debugging
      const data = payload[0].payload;
      console.log('Tooltip Data:', data); // Log the tooltip data for debugging
  
      return (
        <div style={{
          backgroundColor: '#fff',
          border: '1px solid #ccc',
          padding: '10px',
          fontSize: '12px',
          lineHeight: '1.4em',
          borderRadius: '4px',
          textAlign: 'left',
          minWidth: '200px'
        }}>
          {/* Basic Info */}
          <div>
            <strong>Basic Info:</strong>
            {['Solution ID', 'Case Study', 'Location'].map(key => (
              data[key] !== undefined ? (
                <p key={key} style={{ margin: '4px 0', paddingLeft: '10px' }}>
                  {key}: <span style={{ fontWeight: 'normal' }}>{String(data[key])}</span>
                </p>
              ) : null
            ))}
          </div>
  
          {/* Decision Variables */}
          <div style={{ marginTop: '8px' }}>
            <strong>Decision Variables:</strong>
            {decision_keys?.map(key => (
              data[key] !== undefined ? (
                <p key={key} style={{ margin: '4px 0', paddingLeft: '10px' }}>
                  {key}: <span style={{ fontWeight: 'normal' }}>{String(data[key])}</span>
                </p>
              ) : null
            ))}
          </div>
  
          {/* Objective Values */}
          <div style={{ marginTop: '8px' }}>
            <strong>Objectives:</strong>
            {objective_keys?.map(key => (
              data[key] !== undefined ? (
                <p key={key} style={{ margin: '4px 0', paddingLeft: '10px' }}>
                  {key}: <span style={{ fontWeight: 'normal' }}>{String(data[key])}</span>
                </p>
              ) : null
            ))}
          </div>
  
          {/* Weighted Sum and Label */}
          <div style={{ marginTop: '8px' }}>
            <strong>Miscellaneous:</strong>
            {['Weighted Sum', 'label'].map(key => (
              data[key] !== undefined ? (
                <p key={key} style={{ margin: '4px 0', paddingLeft: '10px' }}>
                  {key}: <span style={{ fontWeight: 'normal' }}>{String(data[key])}</span>
                </p>
              ) : null
            ))}
          </div>
        </div>
      );
    }
  
    return null;
  };

  const RenderDot: React.FC<CustomDotProps> = ({
    cx,
    cy,
    fill,
    isTooltipActive,
  }) => {
    console.log(`Rendering dot at (${cx}, ${cy}) with fill: ${fill} and isTooltipActive: ${isTooltipActive}`);
    return (
      <circle
        cx={cx}
        cy={cy}
        r={12}
        fill={fill || '#000'}
        fillOpacity={isTooltipActive ? 1 : 0.6}
        stroke={isTooltipActive ? 'black' : 'none'}
        strokeWidth={isTooltipActive ? 1 : 0}
        style={{
          transition: 'fill-opacity 0.2s ease',
        }}
      />
    );
  };

  const groupedData = React.useMemo(() => {
    if (!hasData || !solutionsData.some(item => labelField in item)) return [];
  
    const groups: Record<string, Solution[]> = {};
  
    solutionsData.forEach(item => {
      const label = item[labelField] as string;
      if (!groups[label]) groups[label] = [];
      groups[label].push(item);
    });
  
    // 🔍 Log each group individually
    Object.entries(groups).forEach(([label, items]) => {
      console.group(`ParallelGroup: ${label} (${items.length} items)`);
      console.log(items); // or console.log for full objects
      console.groupEnd();
    });
  
    return Object.entries(groups).map(([label, data]) => ({
      label,
      data: data.map(datum => ({
        ...datum,
        x: datum[xAxis],
        y: datum[yAxis]
      }))
    }));
  }, [solutionsData, xAxis, yAxis, labelField]); // 👈 Make sure to include labelField in deps

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
        <label style={{ display: 'flex', flexDirection: 'column', fontSize: '16px', fontWeight: 400, color:'#213547',
        fontFamily: 'Inter,system-ui, Avenir, Helvetica,Arial, sans-serif',
          minWidth: '200px',
          flex: 1,
          maxWidth: '250px' }}>
          X-axis:
          <select
            value={xAxis}
            onChange={(e) => setXAxis(e.target.value)}
            style={{ fontSize: '16px', fontWeight: 500, color:'#213547',
            fontFamily: 'Inter,system-ui, Avenir, Helvetica,Arial, sans-serif',width: '100%', maxWidth: '250px', padding: '5px', marginTop: '4px',
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

        <label style={{ display: 'flex', flexDirection: 'column', fontSize: '16px', fontWeight: 400, color:'#213547',
        fontFamily: 'Inter,system-ui, Avenir, Helvetica,Arial, sans-serif',
          minWidth: '200px',
          flex: 1,
          maxWidth: '250px' }}>
          Y-axis:
          <select
            value={yAxis}
            onChange={(e) => setYAxis(e.target.value)}
            style={{ fontSize: '16px', fontWeight: 500, color:'#213547',
            fontFamily: 'Inter,system-ui, Avenir, Helvetica,Arial, sans-serif',width: '100%', maxWidth: '250px', padding: '5px', marginTop: '4px',
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
      <ResponsiveContainer width="100%" height={500}>
        <ScatterChart
          margin={{
            top: 0,
            right: 0,
            bottom: 0,
            left: 0 
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
            hide
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
          <Tooltip content={<CustomTooltip />} cursor={{ strokeDasharray: '3 3' }} />
          {/* <Scatter name={`${xAxis} vs ${yAxis}`} data={formattedData} fill="#8884d8" /> */}
          {/* Render scatter per group */}
          {groupedData.map((group, idx) => ( <Scatter
              key={group.label}
              name={group.label}
              data={group.data}
              fill={COLORS[idx % COLORS.length]}
              // render={(props) => {
              //   const { cx, cy, payload } = props;
              //   const isActive = payload?.isTooltipActive;
            
              //   return <RenderDot cx={cx} cy={cy} fill={COLORS[idx % COLORS.length]} isActive={isActive} />;
              // }}
              shape={<RenderDot fill={COLORS[idx % COLORS.length]}/>}
              // shape={(props) => <RenderDot {...props} fill={COLORS[idx % COLORS.length]} />}
              
            />
          ))}

          {/* Legend at the bottom */}
          {/* <Legend
            layout="horizontal"
            verticalAlign="bottom"
            align="center"
            wrapperStyle={{ fontSize: '12px', bottom: -10}}
            // textStyle={{ fontSize: 2 }}
          /> */}
        </ScatterChart>
      </ResponsiveContainer>
      {objective_keys && (
        <div style={{display:'flex', justifyContent:'center', alignItems:'center', gap:'8px', marginTop:'14px',flexWrap:'wrap', width: '100%'}}>
          {objective_keys.map((obj) =>(
            <span key={obj} style={{display:'flex', alignItems:'center', gap:'6px'}}>
              <span style={{
                width: '14px',
                height: '14px',
                backgroundColor: objectiveColorMap[obj] || '#8884d8',
                borderRadius: '50%',
                display: 'inline-block',
              }}/>
              <span style={{fontSize:'11px', color: objectiveColorMap[obj] || '#8884d8', letterSpacing:0.1, fontWeight:500}}>{obj}</span>
            </span>
          ))}
        </div>
      )}
</div>
  );
};

export default ScatterPlot;