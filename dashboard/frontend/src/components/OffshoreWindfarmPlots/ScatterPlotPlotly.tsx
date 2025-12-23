// components/ScatterPlotPlotly.tsx
import React from 'react';
import Plot from 'react-plotly.js';

// Define Solution type if not already defined elsewhere
export type Solution = Record<string, number | string>;

interface ScatterPlotPlotlyProps {
  useCase: string;
  solutionsData: Solution[];
  decision_keys?: string[];   
  objective_keys?: string[];  
  onColorByChange?: (colorBy: string) => void;
  objectiveColorMap: Record<string, string>;
  colorByField?: string;
}

const COLORS = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96A6C5', '#FAC84D', '#FFA07A', '#8FBC8F'];
  
const ScatterPlotPlotly: React.FC<ScatterPlotPlotlyProps> = ({ 
  solutionsData,
  decision_keys,
  objective_keys,
  onColorByChange,
  objectiveColorMap,
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

  // Helper function to format dollar amounts
  const formatDollarValue = (key: string, value: any) => {
    const stringValue = String(value);
    
    // Check if the key indicates a dollar amount (contains $, cost, price, revenue, etc.)
    const isDollarField = /(\$|cost|price|revenue|budget|capex|opex|lcoe|npv|profit|income|expense)/i.test(key);
    
    if (isDollarField && typeof value === 'number') {
      // Round to nearest hundredth for currency display
      return `$${value.toFixed(2)}`;
    } else if (isDollarField && typeof value === 'string') {
      // Try to parse as number if it's a string representation of a number
      const numValue = parseFloat(stringValue);
      if (!isNaN(numValue)) {
        return `$${numValue.toFixed(2)}`;
      }
    }
    
    // For non-dollar numeric values, check if they're very long decimals and round appropriately
    if (typeof value === 'number' && !Number.isInteger(value)) {
      const decimalPlaces = stringValue.split('.')[1]?.length || 0;
      if (decimalPlaces > 4) {
        return value.toFixed(2);
      }
    }
    
    return stringValue;
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
      console.log(items);
      console.groupEnd();
    });
  
    return Object.entries(groups).map(([label, data], idx) => ({
      x: data.map(datum => datum[xAxis] as number),
      y: data.map(datum => datum[yAxis] as number),
      mode: 'markers' as const,
      type: 'scatter' as const,
      name: label,
      marker: {
        color: COLORS[idx % COLORS.length],
        size: 12,
        opacity: 0.8,
        line: {
          color: 'rgba(0,0,0,0.2)',
          width: 1
        }
      },
      text: data.map(datum => {
        // Create custom hover text
        const basicInfo = ['Solution ID', 'Case Study', 'Location']
          .filter(key => datum[key] !== undefined)
          .map(key => `${key}: ${formatDollarValue(key, datum[key])}`)
          .join('<br>');

        const decisionInfo = decision_keys
          ?.filter(key => datum[key] !== undefined)
          .map(key => `${key}: ${formatDollarValue(key, datum[key])}`)
          .join('<br>') || '';

        const objectiveInfo = objective_keys
          ?.filter(key => datum[key] !== undefined)
          .map(key => `${key}: ${formatDollarValue(key, datum[key])}`)
          .join('<br>') || '';

        const miscInfo = ['Weighted Sum', 'label']
          .filter(key => datum[key] !== undefined)
          .map(key => `${key}: ${formatDollarValue(key, datum[key])}`)
          .join('<br>');

        return [
          basicInfo && `<b>Basic Info:</b><br>${basicInfo}`,
          decisionInfo && `<b>Decision Variables:</b><br>${decisionInfo}`,
          objectiveInfo && `<b>Objectives:</b><br>${objectiveInfo}`,
          miscInfo && `<b>Miscellaneous:</b><br>${miscInfo}`
        ].filter(Boolean).join('<br><br>');
      }),
      hovertemplate: '%{text}<extra></extra>',
      customdata: data // Store original data for reference
    }));
  }, [solutionsData, xAxis, yAxis, labelField, decision_keys, objective_keys]);

  const plotData = groupedData;

  const layout = {
    title: '',
    xaxis: {
      title: xAxis,
      showgrid: true,
      zeroline: false,
    },
    yaxis: {
      title: yAxis,
      showgrid: true,
      zeroline: false,
    },
    hovermode: 'closest' as const,
    showlegend: true,
    legend: {
      x: 1,
      y: 1,
      xanchor: 'left' as const,
      yanchor: 'top' as const,
    },
    margin: {
      l: 50,
      r: 150,
      t: 20,
      b: 50,
    },
    plot_bgcolor: 'rgba(0,0,0,0)',
    paper_bgcolor: 'rgba(0,0,0,0)',
  };

  const config = {
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d', 'autoScale2d'],
    responsive: true,
  };

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
        <label style={{ 
          display: 'flex', 
          flexDirection: 'column', 
          fontSize: '16px', 
          fontWeight: 400, 
          color:'#213547',
          fontFamily: 'Inter,system-ui, Avenir, Helvetica,Arial, sans-serif',
          minWidth: '180px',
          flex: 1,
          maxWidth: '220px' 
        }}>
          X-axis:
          <select
            value={xAxis}
            onChange={(e) => setXAxis(e.target.value)}
            style={{ 
              fontSize: '16px', 
              fontWeight: 500, 
              color:'#213547',
              backgroundColor: '#ffffff',
              border: '1px solid #ccc',
              borderRadius: '4px',
              fontFamily: 'Inter,system-ui, Avenir, Helvetica,Arial, sans-serif',
              width: '100%', 
              maxWidth: '220px', 
              padding: '5px', 
              marginTop: '4px',
              textAlign: 'center',
              textAlignLast: 'center',
            }}
          >
            {numericFields.map((field) => (
              <option key={field} value={field} style={{ backgroundColor: '#ffffff', color: '#213547' }}>
                {field}
              </option>
            ))}
          </select>
        </label>

        <label style={{ 
          display: 'flex', 
          flexDirection: 'column', 
          fontSize: '16px', 
          fontWeight: 400, 
          color:'#213547',
          fontFamily: 'Inter,system-ui, Avenir, Helvetica,Arial, sans-serif',
          minWidth: '180px',
          flex: 1,
          maxWidth: '220px' 
        }}>
          Y-axis:
          <select
            value={yAxis}
            onChange={(e) => setYAxis(e.target.value)}
            style={{ 
              fontSize: '16px', 
              fontWeight: 500, 
              color:'#213547',
              backgroundColor: '#ffffff',
              border: '1px solid #ccc',
              borderRadius: '4px',
              fontFamily: 'Inter,system-ui, Avenir, Helvetica,Arial, sans-serif',
              width: '100%', 
              maxWidth: '220px', 
              padding: '5px', 
              marginTop: '4px',
              textAlign: 'center',
              textAlignLast: 'center',
              colorScheme: 'light'
            }}
          >
            {numericFields.map((field) => (
              <option key={field} value={field} style={{ backgroundColor: '#ffffff', color: '#213547' }}>
                {field}
              </option>
            ))}
          </select>
        </label>

        <label style={{ 
          display: 'flex', 
          flexDirection: 'column', 
          fontSize: '16px', 
          fontWeight: 400, 
          color:'#213547',
          fontFamily: 'Inter,system-ui, Avenir, Helvetica,Arial, sans-serif',
          minWidth: '180px',
          flex: 1,
          maxWidth: '220px' 
        }}>
          Color by:
          <select
            value={labelField}
            onChange={(e) => {
              const newColorBy = e.target.value;
              if (onColorByChange) {
                onColorByChange(newColorBy);
              }
            }}
            style={{ 
              fontSize: '16px', 
              fontWeight: 500, 
              color:'#213547',
              backgroundColor: '#ffffff',
              border: '1px solid #ccc',
              borderRadius: '4px',
              fontFamily: 'Inter,system-ui, Avenir, Helvetica,Arial, sans-serif',
              width: '100%', 
              maxWidth: '220px', 
              padding: '5px', 
              marginTop: '4px',
              textAlign: 'center',
              textAlignLast: 'center',
              colorScheme: 'light'
            }}
          >
            {/* Add common categorical fields for coloring */}
            {hasData && Object.keys(solutionsData[0]).filter(key => 
              key !== 'x_coord' && 
              key !== 'y_coord' && 
              key !== 'sim' && 
              key !== 'time'
            ).map((field) => (
              <option key={field} value={field} style={{ backgroundColor: '#ffffff', color: '#213547' }}>
                {field}
              </option>
            ))}
          </select>
        </label>
      </div>

      {/* Plotly Scatter Chart */}
      <div style={{ width: '100%', height: '500px' }}>
        <Plot
          data={plotData}
          layout={layout}
          config={config}
          style={{ width: '100%', height: '100%' }}
        />
      </div>
      
      {objective_keys && (
        <div style={{
          display:'flex', 
          justifyContent:'center', 
          alignItems:'center', 
          gap:'8px', 
          marginTop:'14px',
          flexWrap:'wrap', 
          width: '100%'
        }}>
          {objective_keys.map((obj) =>(
            <span key={obj} style={{display:'flex', alignItems:'center', gap:'6px'}}>
              <span style={{
                width: '14px',
                height: '14px',
                backgroundColor: objectiveColorMap[obj] || '#8884d8',
                borderRadius: '50%',
                display: 'inline-block',
              }}/>
              <span style={{
                fontSize:'11px', 
                color: objectiveColorMap[obj] || '#8884d8', 
                letterSpacing:0.1, 
                fontWeight:500
              }}>
                {obj}
              </span>
            </span>
          ))}
        </div>
      )}
    </div>
  );
};

export default ScatterPlotPlotly;