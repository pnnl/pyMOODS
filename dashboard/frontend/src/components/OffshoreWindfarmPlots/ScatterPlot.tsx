// components/ScatterPlot.tsx
import React from 'react';
import Plot from 'react-plotly.js';
import { Box, Typography, Select, MenuItem, FormControl, InputLabel } from '@mui/material';
import { COLORS } from '../../utils/colors';
import { getPinnedColor } from '../../utils/pinnedColors';

// Define Solution type if not already defined elsewhere
export type Solution = Record<string, number | string>;

export interface PinnedSolution {
  id: string;
  label: string;
  solution: Solution;
  isFocused: boolean;
}

interface ScatterPlotProps {
  useCase: string;
  solutionsData: Solution[];
  decision_keys?: string[];
  objective_keys?: string[];
  objectiveUnits?: Record<string, string>;
  hyperparameter_keys?: string[];
  input_parameter_keys?: string[];
  onColorByChange?: (colorBy: string) => void;
  objectiveColorMap: Record<string, string>;
  colorByField?: string;
  selectedSolution?: Solution;
  onSolutionSelect?: (solution: Solution) => void;
  pinnedSolutions?: PinnedSolution[];
}

const colorPalette = COLORS;
const PLOT_AXIS_FONT = { size: 13, color: '#213547', family: 'Inter, system-ui, Avenir, Helvetica, Arial, sans-serif' };

const abbrevLabel = (label: string): string => {
  if (label === 'Generalizer') return 'G';
  if (label === 'Specializer') return 'S';
  if (/^Rank\s+\d+$/.test(label)) return `R${label.replace(/\D/g, '')}`;
  return label.slice(0, 2).toUpperCase();
};
  
const ScatterPlot: React.FC<ScatterPlotProps> = ({ 
  solutionsData,
  decision_keys,
  objective_keys,
  objectiveUnits,
  hyperparameter_keys,
  input_parameter_keys,
  onColorByChange,
  objectiveColorMap,
  selectedSolution,
  onSolutionSelect,
  pinnedSolutions,
}) => {

  const hasData = solutionsData.length > 0;

  // Set default values to first two objective functions if available
  const [xAxis, setXAxis] = React.useState(objective_keys?.[0] || 'Expansion Cost');
  const [yAxis, setYAxis] = React.useState(objective_keys?.[1] || 'Expected Datacenter Load Shed');
  const [colorByField, setColorByField] = React.useState(hyperparameter_keys?.[0] || 'Location Scenario');

  // Sync axis selections when the use case changes and new keys arrive
  React.useEffect(() => {
    if (objective_keys && objective_keys.length > 0) {
      setXAxis(objective_keys[0]);
      setYAxis(objective_keys[1] ?? objective_keys[0]);
    }
  }, [objective_keys]);

  React.useEffect(() => {
    if (hyperparameter_keys && hyperparameter_keys.length > 0) {
      setColorByField(hyperparameter_keys[0]);
    }
  }, [hyperparameter_keys]);

  // Track which legend groups are highlighted (empty set = individual solution mode)
  const [highlightedGroups, setHighlightedGroups] = React.useState<Set<string>>(new Set());

  // Reset highlights when data or color field changes
  React.useEffect(() => { setHighlightedGroups(new Set()); }, [solutionsData]);
  React.useEffect(() => { setHighlightedGroups(new Set()); }, [colorByField]);

  // Format legend labels: truncate long floats to 4 sig-figs for readability
  const formatLegendLabel = (name: string) => {
    const n = Number(name);
    if (!isNaN(n) && !Number.isInteger(n) && name.length > 6) {
      return n.toPrecision(4);
    }
    return name;
  };

  const labelField = colorByField;

  const currencyFormatter = React.useMemo(
    () =>
      new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }),
    []
  );

  // Helper function to format dollar amounts
  const formatDollarValue = (key: string, value: any) => {
    const stringValue = String(value);
    
    // Check if the key indicates a dollar amount (contains $, cost, price, revenue, etc.)
    const isDollarField = /(\$|cost|price|revenue|budget|capex|opex|lcoe|npv|profit|income|expense)/i.test(key);
    
    if (isDollarField && typeof value === 'number') {
      // Format currency with thousands separators
      return currencyFormatter.format(value);
    } else if (isDollarField && typeof value === 'string') {
      // Try to parse as number if it's a string representation of a number
      const numValue = parseFloat(stringValue);
      if (!isNaN(numValue)) {
        return currencyFormatter.format(numValue);
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

  const getObjectiveLabelWithUnit = (key: string) => {
    const unit = objectiveUnits?.[key];
    return unit ? `${key} (${unit})` : key;
  };

  const getNumericValuesForField = (field: string) =>
    solutionsData
      .map((datum) => Number(datum[field]))
      .filter((value) => Number.isFinite(value));

  const getNiceTickStep = (minValue: number, maxValue: number, targetTickCount = 6) => {
    const span = Math.abs(maxValue - minValue);
    if (!Number.isFinite(span) || span === 0) return 1;

    const rawStep = span / Math.max(targetTickCount - 1, 1);
    const magnitude = Math.pow(10, Math.floor(Math.log10(rawStep)));
    const normalized = rawStep / magnitude;

    let niceNormalized = 1;
    if (normalized <= 1) niceNormalized = 1;
    else if (normalized <= 2) niceNormalized = 2;
    else if (normalized <= 5) niceNormalized = 5;
    else niceNormalized = 10;

    return niceNormalized * magnitude;
  };

  const getAxisConfigForField = (field: string) => {
    const values = getNumericValuesForField(field);
    const unit = objectiveUnits?.[field];

    if (values.length === 0) {
      return {
        tickmode: 'auto' as const,
        tick0: undefined,
        dtick: undefined,
        tickformat: unit === 'USD' ? '$,.0f' : ',.2f',
      };
    }

    const minValue = Math.min(...values);
    const maxValue = Math.max(...values);
    const dtick = getNiceTickStep(minValue, maxValue);
    const tick0 = Math.floor(minValue / dtick) * dtick;

    let tickformat = ',.2f';
    if (unit === 'USD') {
      tickformat = dtick >= 1 ? '$,.0f' : '$,.2f';
    } else if (dtick >= 1) {
      tickformat = ',.0f';
    }

    return {
      tickmode: 'linear' as const,
      tick0,
      dtick,
      tickformat,
    };
  };

  const xAxisConfig = React.useMemo(() => getAxisConfigForField(xAxis), [solutionsData, xAxis, objectiveUnits]);
  const yAxisConfig = React.useMemo(() => getAxisConfigForField(yAxis), [solutionsData, yAxis, objectiveUnits]);

  const groupedData = React.useMemo(() => {
    if (!hasData || !solutionsData.some(item => labelField in item)) return [];
  
    const groups: Record<string, Solution[]> = {};
  
    solutionsData.forEach(item => {
      const label = item[labelField] as string;
      if (!groups[label]) groups[label] = [];
      groups[label].push(item);
    });
  
    return Object.entries(groups).map(([label, data], idx) => ({
      x: data.map(datum => datum[xAxis] as number),
      y: data.map(datum => datum[yAxis] as number),
      mode: 'markers' as const,
      type: 'scatter' as const,
      name: label,
      marker: {
        color: objectiveColorMap[label] || colorPalette[idx % colorPalette.length],
        size: 12,
        opacity: 0.8,
        line: {
          color: 'rgba(0,0,0,0.2)',
          width: 1
        }
      },
      text: data.map(datum => {
        // Create custom hover text
        // Dynamically find basic info fields including location fields
        const basicInfoFields = ['Solution ID', 'Case Study', 'Location', 'Location Scenario']
          .filter(key => datum[key] !== undefined);
        
        const basicInfo = basicInfoFields
          .map(key => `${key}: ${formatDollarValue(key, datum[key])}`)
          .join('<br>');

        const decisionInfo = decision_keys
          ?.filter(key => datum[key] !== undefined)
          .map(key => `${key}: ${formatDollarValue(key, datum[key])}`)
          .join('<br>') || '';

        const objectiveInfo = objective_keys
          ?.filter(key => datum[key] !== undefined)
          .map(key => `${getObjectiveLabelWithUnit(key)}: ${formatDollarValue(key, datum[key])}`)
          .join('<br>') || '';

        // Combine input parameters and hyperparameters
        const allParameterKeys = [
          ...(input_parameter_keys || []),
          ...(hyperparameter_keys || [])
        ];
        const parametersInfo = allParameterKeys
          .filter(key => datum[key] !== undefined)
          .map(key => `${key}: ${formatDollarValue(key, datum[key])}`)
          .join('<br>');

        const miscInfo = ['Weighted Sum', 'label']
          .filter(key => datum[key] !== undefined)
          .map(key => `${key}: ${formatDollarValue(key, datum[key])}`)
          .join('<br>');

        return [
          basicInfo && `<b>Basic Info:</b><br>${basicInfo}`,
          decisionInfo && `<b>Decision Variables:</b><br>${decisionInfo}`,
          objectiveInfo && `<b>Objectives:</b><br>${objectiveInfo}`,
          parametersInfo && `<b>Parameters:</b><br>${parametersInfo}`,
          miscInfo && `<b>Miscellaneous:</b><br>${miscInfo}`
        ].filter(Boolean).join('<br><br>');
      }),
      hovertemplate: '%{text}<extra></extra>',
      customdata: data as any // Store original data for reference
    }));
  }, [solutionsData, xAxis, yAxis, labelField, decision_keys, objective_keys, objectiveUnits, hyperparameter_keys, input_parameter_keys, currencyFormatter]);

  // Build the final plot data with highlight/gray logic
  const plotData = React.useMemo(() => {
    if (!hasData || groupedData.length === 0) return groupedData;

    const effectiveSolution = selectedSolution ?? (solutionsData.length > 0 ? solutionsData[0] : null);
    const isGroupMode = highlightedGroups.size > 0;

    // Base traces: full color by default; gray non-highlighted groups in group mode
    const baseTraces = groupedData.map((trace, idx) => {
      const baseColor = colorPalette[idx % colorPalette.length];
      if (isGroupMode) {
        const isHighlighted = highlightedGroups.has(trace.name);
        return {
          ...trace,
          marker: {
            ...trace.marker,
            color: isHighlighted ? baseColor : '#c8c8c8',
            opacity: isHighlighted ? 0.8 : 0.2,
            size: isHighlighted ? 12 : 8,
          },
        };
      }
      // Default: all points shown with their group color, slightly dimmed
      return {
        ...trace,
        marker: {
          ...trace.marker,
          color: baseColor,
          size: 9,
          opacity: 0.4,
          line: { color: 'rgba(0,0,0,0.1)', width: 1 },
        },
      };
    });

    // Helper: build detailed hover text for any solution object
    const buildHoverText = (datum: Solution) => {
      const basicInfoFields = ['Solution ID', 'Case Study', 'Location', 'Location Scenario']
        .filter(key => datum[key] !== undefined);
      const basicInfo = basicInfoFields
        .map(key => `${key}: ${formatDollarValue(key, datum[key])}`).join('<br>');
      const decisionInfo = decision_keys
        ?.filter(key => datum[key] !== undefined)
        .map(key => `${key}: ${formatDollarValue(key, datum[key])}`).join('<br>') || '';
      const objectiveInfo = objective_keys
        ?.filter(key => datum[key] !== undefined)
        .map(key => `${getObjectiveLabelWithUnit(key)}: ${formatDollarValue(key, datum[key])}`).join('<br>') || '';
      const allParameterKeys = [...(input_parameter_keys || []), ...(hyperparameter_keys || [])];
      const parametersInfo = allParameterKeys
        .filter(key => datum[key] !== undefined)
        .map(key => `${key}: ${formatDollarValue(key, datum[key])}`).join('<br>');
      const miscInfo = ['Weighted Sum', 'label']
        .filter(key => datum[key] !== undefined)
        .map(key => `${key}: ${formatDollarValue(key, datum[key])}`).join('<br>');
      return [
        basicInfo && `<b>Basic Info:</b><br>${basicInfo}`,
        decisionInfo && `<b>Decision Variables:</b><br>${decisionInfo}`,
        objectiveInfo && `<b>Objectives:</b><br>${objectiveInfo}`,
        parametersInfo && `<b>Parameters:</b><br>${parametersInfo}`,
        miscInfo && `<b>Miscellaneous:</b><br>${miscInfo}`,
      ].filter(Boolean).join('<br><br>');
    };

    // ── Comparison-table mode: render a labeled marker for every pinned solution ──
    if (pinnedSolutions && pinnedSolutions.length > 0) {
      const pinnedTraces = pinnedSolutions.flatMap((pinned, i) => {
        const x = Number(pinned.solution[xAxis]);
        const y = Number(pinned.solution[yAxis]);
        if (!isFinite(x) || !isFinite(y)) return [];

        const color = getPinnedColor(i);
        const focused = pinned.isFocused;
        const ringSize = focused ? 34 : 24;
        const dotSize  = focused ? 16 : 11;
        const border   = focused ? 2.5 : 2;
        const abbrev   = abbrevLabel(pinned.label);
        const hoverText = `<b>${pinned.label}</b><br>${buildHoverText(pinned.solution)}`;

        return [
          // Outer ring (transparent fill, colored border)
          {
            x: [x], y: [y],
            mode: 'markers' as const,
            type: 'scatter' as const,
            name: pinned.label,
            showlegend: false,
            hovertemplate: '<extra></extra>',
            marker: {
              color: 'rgba(0,0,0,0)',
              size: ringSize,
              opacity: 1,
              line: { color, width: border },
            },
          },
          // Solid dot + abbreviated label above
          {
            x: [x], y: [y],
            mode: 'markers+text' as any,
            type: 'scatter' as const,
            name: pinned.label,
            showlegend: false,
            text: [abbrev],
            textposition: 'top center' as const,
            textfont: { size: 10, color, family: PLOT_AXIS_FONT.family },
            hovertemplate: `${hoverText}<extra></extra>`,
            marker: {
              color,
              size: dotSize,
              symbol: 'circle' as const,
              opacity: 1,
              line: { color: '#fff', width: border },
            },
            customdata: [pinned.solution] as any,
          },
        ];
      });

      return [...baseTraces, ...pinnedTraces];
    }

    // ── Single-selection mode (fallback): highlight one solution with a halo ──
    if (effectiveSolution) {
      const groupLabel = effectiveSolution[labelField] as string;
      const groupIdx = groupedData.findIndex(t => t.name === groupLabel);
      const groupColor = colorPalette[Math.max(0, groupIdx) % colorPalette.length];
      const hoverText = buildHoverText(effectiveSolution);

      const haloTrace = {
        x: [effectiveSolution[xAxis] as number],
        y: [effectiveSolution[yAxis] as number],
        mode: 'markers' as const,
        type: 'scatter' as const,
        name: 'Selected Halo',
        showlegend: false,
        hovertemplate: '<extra></extra>',
        text: [] as string[],
        customdata: [] as any,
        marker: {
          color: 'rgba(0,0,0,0)',
          size: 32,
          opacity: 1,
          line: { color: groupColor, width: 2.5 },
        },
      };

      const selectedTrace = {
        x: [effectiveSolution[xAxis] as number],
        y: [effectiveSolution[yAxis] as number],
        mode: 'markers' as const,
        type: 'scatter' as const,
        name: 'Selected',
        showlegend: false,
        marker: {
          color: groupColor,
          size: 16,
          symbol: 'circle' as const,
          opacity: 1,
          line: { color: '#fff', width: 2.5 },
        },
        text: [hoverText],
        hovertemplate: '%{text}<extra></extra>',
        customdata: [effectiveSolution] as any,
      };

      return [...baseTraces, haloTrace, selectedTrace];
    }

    return baseTraces;
  }, [groupedData, selectedSolution, highlightedGroups, solutionsData, xAxis, yAxis, labelField, objectiveColorMap, decision_keys, objective_keys, hyperparameter_keys, input_parameter_keys, pinnedSolutions]);

  // Click handler: select the clicked solution
  const handlePlotClick = React.useCallback((event: any) => {
    if (!event.points || event.points.length === 0) return;
    const solution = event.points[0].customdata;
    if (!solution) return;
    setHighlightedGroups(new Set());
    if (onSolutionSelect) onSolutionSelect(solution);
  }, [onSolutionSelect]);

  // Legend click handler: toggle group highlight (multi-select)
  const handleLegendClick = React.useCallback((event: any): boolean => {
    const traceName = event.data?.[event.curveNumber]?.name;
    if (!traceName || traceName === 'Selected') return false;
    setHighlightedGroups(prev => {
      const next = new Set(prev);
      if (next.has(traceName)) {
        next.delete(traceName);
      } else {
        next.add(traceName);
      }
      return next;
    });
    return false; // Prevent Plotly's default toggle behavior
  }, []);

  const layout = {
    title: { text: '' },
    xaxis: {
      title: { text: getObjectiveLabelWithUnit(xAxis), font: PLOT_AXIS_FONT },
      showgrid: true,
      showline: true,
      ticks: 'outside' as const,
      ticklen: 6,
      tickwidth: 1,
      tickcolor: '#213547',
      zeroline: false,
      showticklabels: true,
      automargin: true,
      tickmode: xAxisConfig.tickmode,
      tick0: xAxisConfig.tick0,
      dtick: xAxisConfig.dtick,
      tickformat: xAxisConfig.tickformat,
    },
    yaxis: {
      title: { text: getObjectiveLabelWithUnit(yAxis), font: PLOT_AXIS_FONT },
      showgrid: true,
      showline: true,
      ticks: 'outside' as const,
      ticklen: 6,
      tickwidth: 1,
      tickcolor: '#213547',
      zeroline: false,
      showticklabels: true,
      tickmode: yAxisConfig.tickmode,
      tick0: yAxisConfig.tick0,
      dtick: yAxisConfig.dtick,
      tickformat: yAxisConfig.tickformat,
    },
    hovermode: 'closest' as const,
    hoverlabel: {
      bgcolor: '#ffffff',
      bordercolor: '#cccccc',
      font: { color: '#213547' }
    },
    showlegend: false,
    margin: { l: 56, r: 16, t: 20, b: 60 },
    plot_bgcolor: 'rgba(0,0,0,0)',
    paper_bgcolor: 'rgba(0,0,0,0)',
  };

  const config = {
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: [ 'lasso2d', 'select2d', 'autoScale2d'] as any,
    responsive: true,
  };

  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        margin: '0px',
        padding: '0px',
        display: 'flex',
        flexDirection: 'column',
        minHeight: 0,
      }}
    >
      {/* Chart axis controls — MUI selects inside a branded toolbar */}
      <div style={{ display: 'flex', gap: '8px', marginTop: '8px', marginBottom: '8px', flexWrap: 'wrap', alignItems: 'center', background: 'rgba(27,41,59,0.04)', border: '1px solid rgba(27,41,59,0.10)', borderRadius: '8px', padding: '6px 12px' }}>
        <FormControl size="small" sx={{ flex: 1, minWidth: 120, maxWidth: 180 }}>
          <InputLabel sx={{ fontSize: '0.875rem' }}>X-axis</InputLabel>
          <Select
            value={xAxis}
            label="X-axis"
            onChange={(e) => setXAxis(e.target.value)}
            sx={{ fontSize: '0.875rem', bgcolor: '#fff' }}
          >
            {(objective_keys || []).map((field) => (
              <MenuItem key={field} value={field} sx={{ fontSize: '0.875rem' }}>{field}</MenuItem>
            ))}
          </Select>
        </FormControl>

        <FormControl size="small" sx={{ flex: 1, minWidth: 120, maxWidth: 180 }}>
          <InputLabel sx={{ fontSize: '0.875rem' }}>Y-axis</InputLabel>
          <Select
            value={yAxis}
            label="Y-axis"
            onChange={(e) => setYAxis(e.target.value)}
            sx={{ fontSize: '0.875rem', bgcolor: '#fff' }}
          >
            {(objective_keys || []).map((field) => (
              <MenuItem key={field} value={field} sx={{ fontSize: '0.875rem' }}>{field}</MenuItem>
            ))}
          </Select>
        </FormControl>

        <FormControl size="small" sx={{ flex: 1, minWidth: 120, maxWidth: 180 }}>
          <InputLabel sx={{ fontSize: '0.875rem' }}>Color by</InputLabel>
          <Select
            value={colorByField}
            label="Color by"
            onChange={(e) => {
              const newColorBy = e.target.value;
              setColorByField(newColorBy);
              if (onColorByChange) onColorByChange(newColorBy);
            }}
            sx={{ fontSize: '0.875rem', bgcolor: '#fff' }}
          >
            {(hyperparameter_keys || []).map((field) => (
              <MenuItem key={field} value={field} sx={{ fontSize: '0.875rem' }}>{field}</MenuItem>
            ))}
          </Select>
        </FormControl>
      </div>

      {/* Legend — single row, horizontally scrollable, fixed height regardless of item count.
           Never wraps to multiple rows, so the chart below always gets consistent height. */}
      {groupedData.length > 0 && (
        <Box
          sx={{
            display: 'flex',
            flexWrap: 'nowrap',        // ← single row, no height change when items are added
            alignItems: 'center',
            gap: '12px',
            px: 1.5,
            py: 0.75,
            mb: 0.75,
            flexShrink: 0,             // ← never donate height to the chart flex sibling
            bgcolor: 'rgba(255,255,255,0.95)',
            border: '1px solid',
            borderColor: 'divider',
            borderRadius: 1.5,
            overflowX: 'auto',         // ← scroll when items overflow the row
            scrollbarWidth: 'thin',
            scrollbarColor: 'rgba(0,0,0,0.15) transparent',
            '&::-webkit-scrollbar': { height: 4 },
            '&::-webkit-scrollbar-thumb': { bgcolor: 'rgba(0,0,0,0.15)', borderRadius: 2 },
          }}
        >
          <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 600, flexShrink: 0, whiteSpace: 'nowrap' }}>
            {colorByField}:
          </Typography>
          {groupedData.map((trace, idx) => {
            const color = colorPalette[idx % colorPalette.length];
            const isActive = highlightedGroups.size === 0 || highlightedGroups.has(trace.name);
            return (
              <Box
                key={trace.name}
                onClick={() =>
                  setHighlightedGroups(prev => {
                    const next = new Set(prev);
                    if (next.has(trace.name)) next.delete(trace.name);
                    else next.add(trace.name);
                    return next;
                  })
                }
                sx={{
                  display: 'flex', alignItems: 'center', gap: '5px',
                  flexShrink: 0,          // ← items never compress; row scrolls instead
                  cursor: 'pointer',
                  opacity: isActive ? 1 : 0.35,
                  transition: 'opacity 0.15s',
                  '&:hover': { opacity: 1 },
                }}
              >
                <Box sx={{ width: 10, height: 10, borderRadius: '50%', bgcolor: color, border: '1.5px solid rgba(0,0,0,0.12)', flexShrink: 0 }} />
                <Typography variant="caption" sx={{ fontSize: '0.8rem', color: 'text.primary', fontWeight: 500, lineHeight: 1, whiteSpace: 'nowrap' }}>
                  {formatLegendLabel(trace.name)}
                </Typography>
              </Box>
            );
          })}
          {highlightedGroups.size > 0 && (
            <Typography
              variant="caption"
              onClick={() => setHighlightedGroups(new Set())}
              sx={{ ml: 'auto', fontSize: '0.72rem', color: 'text.secondary', cursor: 'pointer', flexShrink: 0, '&:hover': { color: 'text.primary' } }}
            >
              Clear
            </Typography>
          )}
        </Box>
      )}

      {/* Plotly Scatter Chart — minHeight ensures axes are never clipped when panel is short */}
      <div style={{ width: '100%', flex: 1, minHeight: 200 }}>
        <Plot
          data={plotData}
          layout={layout}
          config={config}
          onClick={handlePlotClick}
          onLegendClick={handleLegendClick}
          style={{ width: '100%', height: '100%' }}
        />
      </div>
    </div>
  );
};

export default ScatterPlot;