import React, { useEffect, useRef, useState } from 'react';
import { Box } from '@mui/material';
import * as d3 from 'd3';
import config from '../../config';
import { COLORS } from '../../utils/colors';
import { getPinnedColor } from '../../utils/pinnedColors';

const CHART_FONT = 'Inter, system-ui, Avenir, Helvetica, Arial, sans-serif';
const AXIS_TEXT_COLOR = '#000000';
const PCP_GENERALIZER_COUNT = 10;
const PCP_HIGHLIGHT_COLOR = COLORS[0];

const { API_BASE_URL } = config;

// Define types
interface RankDict {
  [key: string]: Record<string, number>;
}

interface ObjectiveFlagDict {
  [solutionKey: string]: Record<string, boolean>;
}

interface SolutionDetailDict {
  [solutionKey: string]: Record<string, string | number | null>;
}

interface ParallelCoordinatesChartProps {
  ranks: RankDict;
  useCase?: string;
  filters?: Record<string, string[]>;
  weights?: Record<string, number>;
  selectedSolutions?: Array<Record<string, string | number | null>>;
  focusedSolution?: Record<string, string | number | null>;
}

const ParallelCoordinatesChart: React.FC<ParallelCoordinatesChartProps> = ({ 
  ranks, 
  useCase,
  filters = {},
  weights = {},
  selectedSolutions = [],
  focusedSolution,
}) => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const ref = useRef<SVGSVGElement | null>(null);
  const [currentRanks, setCurrentRanks] = useState<RankDict>({});
  const [generalizerKey, setGeneralizerKey] = useState<string | null>(null);
  const [specializationMatrix, setSpecializationMatrix] = useState<ObjectiveFlagDict>({});
  const [tradeoffMatrix, setTradeoffMatrix] = useState<ObjectiveFlagDict>({});
  const [solutionDetailsByKey, setSolutionDetailsByKey] = useState<SolutionDetailDict>({});
  const [decisionKeys, setDecisionKeys] = useState<string[]>([]);
  const [objectiveKeys, setObjectiveKeys] = useState<string[]>([]);
  const [hyperparameterKeys, setHyperparameterKeys] = useState<string[]>([]);
  const [inputParameterKeys, setInputParameterKeys] = useState<string[]>([]);
  const [objectiveUnits, setObjectiveUnits] = useState<Record<string, string | null>>({});

  const getSolutionIdentity = (solution: Record<string, unknown> | null | undefined): string | null => {
    if (!solution) return null;
    const raw = solution['Solution ID'] ?? solution['solution_id'];
    if (raw === undefined || raw === null) return null;
    return String(raw);
  };

  const selectedSolutionIds = new Set(
    selectedSolutions
      .map((solution) => getSolutionIdentity(solution as Record<string, unknown>))
      .filter((id): id is string => Boolean(id)),
  );

  const selectedSolutionColorById = new Map(
    selectedSolutions
      .map((solution, index) => {
        const id = getSolutionIdentity(solution as Record<string, unknown>);
        return id ? ([id, getPinnedColor(index)] as const) : null;
      })
      .filter((entry): entry is readonly [string, string] => Boolean(entry)),
  );

  const focusedSolutionId = getSolutionIdentity(focusedSolution as Record<string, unknown> | undefined);

  // Flatten rank data from API
  const processData = () => {
    const dataToProcess = currentRanks;
    if (!dataToProcess || Object.keys(dataToProcess).length === 0) return { rankedData: [], numericColumns: [] };

    const flatData = Object.entries(dataToProcess).map(([key, values]) => {
      const parts = key.split(',').map((part) => part.trim()).filter(Boolean);
      const config = parts[0] || key;
      const site = parts[1] || '';
      return {
        _key: key,
        config,
        site,
        ...values,
      };
    }) as Array<{ _key: string; config: string; site: string; [key: string]: any }>;

    const numericColumns = Object.keys(flatData[0]).filter(
      key => typeof flatData[0][key] === 'number'
    );

    return { rankedData: flatData, numericColumns };
  };

  const draw = () => {
    const svg = d3.select(ref.current);
    svg.selectAll('*').remove(); // Clear previous content
    d3.selectAll('.pcp-tooltip').remove();

    const boundingRect = containerRef.current?.getBoundingClientRect();
    const rawWidth = boundingRect && boundingRect.width > 0 ? boundingRect.width : 900;
    const containerWidth = Math.min(rawWidth, 600);
    const containerHeight = boundingRect && boundingRect.height > 0 ? boundingRect.height : 400;

    const margin = { top: 20, right: 10, bottom: 80, left: 40 };
    const width = containerWidth - margin.left - margin.right;
    const height = containerHeight - margin.top - margin.bottom;

    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    const { rankedData, numericColumns } = processData();
    if (!rankedData.length) return;

    const rankColumns = numericColumns;

    // Create scales
    const yScales: Record<string, d3.ScaleLinear<number, number>> = {};
    const xScale = d3.scalePoint()
      .domain(rankColumns)
      .range([0, width])
      .padding(0.35);

    rankColumns.forEach(col => {
      yScales[col] = d3.scaleLinear()
        .domain([1, 10])
        .range([1, height])
        .clamp(true);
    });

    const lineGenerator = d3.line<[number, number]>()
      .x(point => point[0])
      .y(point => point[1]);

    const getLinePoints = (row: { [key: string]: any }): [number, number][] => {
      return rankColumns.map((dim) => {
        const rankValue = Number(row[dim]);
        const clampedRank = Number.isFinite(rankValue)
          ? Math.max(1, Math.min(10, rankValue))
          : 1;

        return [xScale(dim) ?? 0, yScales[dim](clampedRank)];
      });
    };

    const escapeHtml = (value: unknown): string =>
      String(value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');

    const currencyRegex = /(\$|cost|price|revenue|budget|capex|opex|lcoe|npv|profit|income|expense)/i;

    const formatValue = (key: string, raw: unknown): string => {
      if (raw === null || raw === undefined) return '—';
      const asNumber = Number(raw);
      if (currencyRegex.test(key) && Number.isFinite(asNumber)) {
        return asNumber.toLocaleString('en-US', {
          style: 'currency',
          currency: 'USD',
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        });
      }
      if (Number.isFinite(asNumber) && !Number.isInteger(asNumber)) {
        return asNumber.toFixed(2);
      }
      return String(raw);
    };

    const objectiveLabelWithUnit = (key: string): string => {
      const unit = objectiveUnits[key];
      return unit ? `${key} (${unit})` : key;
    };

    const buildDetailedTooltipHtml = (row: { _key: string; config: string; site: string }): string => {
      const detail = solutionDetailsByKey[row._key];
      if (!detail) {
        const label = row.site ? `${row.config} - ${row.site}` : row.config;
        return `<b>${escapeHtml(label)}</b>`;
      }

      const basicFields = ['Solution ID', 'Case Study', 'Location', 'Location Scenario'];
      const basicRows = basicFields
        .filter((field) => detail[field] !== undefined)
        .map((field) => `${escapeHtml(field)}: ${escapeHtml(formatValue(field, detail[field]))}`)
        .join('<br/>');

      const decisionRows = decisionKeys
        .filter((field) => detail[field] !== undefined)
        .map((field) => `${escapeHtml(field)}: ${escapeHtml(formatValue(field, detail[field]))}`)
        .join('<br/>');

      const objectiveRows = objectiveKeys
        .filter((field) => detail[field] !== undefined)
        .map((field) => `${escapeHtml(objectiveLabelWithUnit(field))}: ${escapeHtml(formatValue(field, detail[field]))}`)
        .join('<br/>');

      const parameterKeys = [...inputParameterKeys, ...hyperparameterKeys];
      const parameterRows = parameterKeys
        .filter((field) => detail[field] !== undefined)
        .map((field) => `${escapeHtml(field)}: ${escapeHtml(formatValue(field, detail[field]))}`)
        .join('<br/>');

      const miscRows = ['Weighted Sum', 'label']
        .filter((field) => detail[field] !== undefined)
        .map((field) => `${escapeHtml(field)}: ${escapeHtml(formatValue(field, detail[field]))}`)
        .join('<br/>');

      const sections = [
        basicRows && `<b>Basic Info:</b><br/>${basicRows}`,
        decisionRows && `<b>Decision Variables:</b><br/>${decisionRows}`,
        objectiveRows && `<b>Objectives:</b><br/>${objectiveRows}`,
        parameterRows && `<b>Parameters:</b><br/>${parameterRows}`,
        miscRows && `<b>Miscellaneous:</b><br/>${miscRows}`,
      ].filter(Boolean);

      return sections.join('<br/><br/>') || `<b>${escapeHtml(row.config)}</b>`;
    };

    // Tooltip
    const tooltip = d3.select('body').append('div')
      .attr('class', 'pcp-tooltip')
      .style('position', 'absolute')
      .style('text-align', 'left')
      .style('width', '250px')
      .style('max-width', '42vw')
      .style('max-height', '400px')
      .style('overflow-y', 'auto')
      .style('height', 'auto')
      .style('padding', '8px 10px')
      .style('font-size', '0.8rem')
      .style('font-family', CHART_FONT)
      .style('background', '#ffffff')
      .style('border', '1px solid #cccccc')
      .style('border-radius', '4px')
      .style('opacity', 0)
      .style('pointer-events', 'none')
      .style('z-index', '2000')
      .style('color', '#213547');

    const isGeneralizerLine = (row: { _key: string }) =>
      generalizerKey !== null && row._key === generalizerKey;

    const getLineSelectionState = (row: { _key: string }): 'focused' | 'pinned' | 'default' => {
      const detail = solutionDetailsByKey[row._key] as Record<string, unknown> | undefined;
      const solutionId = getSolutionIdentity(detail);

      if (solutionId && focusedSolutionId && solutionId === focusedSolutionId) {
        return 'focused';
      }

      if (solutionId && selectedSolutionIds.has(solutionId)) {
        return 'pinned';
      }

      return 'default';
    };

    const getLineSelectionColor = (row: { _key: string }): string | null => {
      const detail = solutionDetailsByKey[row._key] as Record<string, unknown> | undefined;
      const solutionId = getSolutionIdentity(detail);
      if (!solutionId) return null;
      return selectedSolutionColorById.get(solutionId) ?? null;
    };

    const getLineColor = (row: { _key: string }) => {
      if (isGeneralizerLine(row)) return PCP_HIGHLIGHT_COLOR;
      const selectedColor = getLineSelectionColor(row);
      if (selectedColor) return selectedColor;
      return '#b9bec7';
    };

    const getLineWidth = (row: { _key: string }) => {
      if (isGeneralizerLine(row)) return 4;
      if (getLineSelectionState(row) === 'focused') return 4.8;
      if (getLineSelectionState(row) === 'pinned') return 3.2;
      return 1.5;
    };

    const getLineOpacity = (row: { _key: string }) => {
      if (isGeneralizerLine(row)) return 1;
      if (getLineSelectionState(row) !== 'default') return 1;
      return 0.55;
    };

    const getSortWeight = (row: { _key: string }) => {
      const selectionState = getLineSelectionState(row);
      if (isGeneralizerLine(row)) return 3;
      if (selectionState === 'focused') return 2;
      if (selectionState === 'pinned') return 1;
      return 0;
    };

    const sortedRankedData = [...rankedData].sort(
      (a, b) => getSortWeight(a) - getSortWeight(b),
    );

    // Draw lines
    g.selectAll('.line')
      .data(sortedRankedData)
      .enter()
      .append('path')
      .attr('class', d => `line ${d.config.replace(/\s+/g, '')}`)
      .attr('fill', 'none')
      .attr('stroke', d => getLineColor(d))
      .attr('stroke-opacity', d => getLineOpacity(d))
      .attr('stroke-width', d => getLineWidth(d))
      .attr('d', d => lineGenerator(getLinePoints(d)) ?? '')
      .on('mouseover', function(event, d) {
        const baseWidth = getLineWidth(d);
        d3.select(this)
          .attr('stroke-width', baseWidth + 1)
          .attr('stroke-opacity', 1)
          .raise();

        const selectionState = getLineSelectionState(d);
        const tag = isGeneralizerLine(d)
          ? '<br/><b>Type:</b> Generalizer'
          : selectionState === 'focused'
          ? '<br/><b>Type:</b> Selected'
          : selectionState === 'pinned'
          ? '<br/><b>Type:</b> Pinned'
          : '';
        const detailedHtml = buildDetailedTooltipHtml(d);
        tooltip.interrupt();
        tooltip.transition().duration(120).style('opacity', .9);
        tooltip.html(`<div style="color: #213547; line-height: 1.35;">${detailedHtml}${tag}</div>`)
                 .style('left', (event.pageX + 10) + 'px')
                 .style('top', (event.pageY - 28) + 'px');
      })
      .on('mouseout', function(_event, d) {
        d3.select(this)
          .attr('stroke-width', getLineWidth(d))
          .attr('stroke-opacity', getLineOpacity(d));
        tooltip.interrupt();
        tooltip.transition().duration(120).style('opacity', 0);
      });

    svg.on('mouseleave', () => {
      tooltip.interrupt();
      tooltip.style('opacity', 0);
    });

    d3.select(containerRef.current).on('mouseleave.pcp-tooltip', () => {
      tooltip.interrupt();
      tooltip.style('opacity', 0);
    });

    // Axis guide lines
    rankColumns.forEach((col) => {
      g.append('line')
        .attr('x1', xScale(col) ?? 0)
        .attr('x2', xScale(col) ?? 0)
        .attr('y1', 0)
        .attr('y2', height)
        .attr('stroke', '#eee');
    });

    const markerData = sortedRankedData.flatMap((row) =>
      getLinePoints(row).map(([x, y], objectiveIndex) => {
        const objectiveKey = rankColumns[objectiveIndex];
        const hasSpecialization = Boolean(specializationMatrix[row._key]?.[objectiveKey]);
        const hasTradeoff = Boolean(tradeoffMatrix[row._key]?.[objectiveKey]);

        return {
        key: row._key,
        x,
        y,
        hasSpecialization,
        hasTradeoff,
        isGeneralizer: isGeneralizerLine(row),
        selectionState: getLineSelectionState(row),
        };
      }),
    ).filter((point) => point.hasSpecialization || point.hasTradeoff);

    const markerSymbol = d3.symbol<{
      hasSpecialization: boolean;
      hasTradeoff: boolean;
      isGeneralizer: boolean;
      selectionState: 'focused' | 'pinned' | 'default';
    }>()
      .type((d) => (d.hasTradeoff ? d3.symbolSquare : d3.symbolCircle))
      .size((d) => (d.selectionState === 'focused' ? 86 : d.isGeneralizer ? 72 : d.selectionState === 'pinned' ? 68 : 54));

    // Draw an opaque marker at each objective-axis intersection for every line.
    g.selectAll('.pcp-marker')
      .data(markerData)
      .enter()
      .append('path')
      .attr('class', d => `pcp-marker pcp-marker-${d.key.replace(/\s+/g, '')}`)
      .attr('d', markerSymbol)
      .attr('transform', d => `translate(${d.x},${d.y})`)
      .attr('fill', d => (
        d.isGeneralizer
          ? PCP_HIGHLIGHT_COLOR
          : getLineSelectionColor({ _key: d.key })
          ? getLineSelectionColor({ _key: d.key })
          : '#c6ccd5'
      ))
      .attr('fill-opacity', 1)
      .attr('stroke', d => (d.isGeneralizer || d.selectionState !== 'default' ? '#ffffff' : '#7f8b99'))
      .attr('stroke-opacity', 1)
      .attr('stroke-width', d => (d.isGeneralizer ? 1.3 : d.selectionState === 'focused' ? 1.8 : d.selectionState === 'pinned' ? 1.4 : 1))
      .style('pointer-events', 'none');

    // Y-axis on first dimension
    const firstDim = rankColumns[0];
    const firstAxisX = xScale(firstDim) ?? 0;

    // Fixed even-number ticks as requested.
    const tickValues = [2, 4, 6, 8, 10];

    const yAxisGroup = g.append('g')
      .attr('transform', `translate(${firstAxisX},0)`)
      .call(
        d3.axisLeft(yScales[firstDim])
          .tickValues(tickValues)
          .tickFormat(d3.format('d'))
      );

    yAxisGroup.selectAll('.tick text')
      .style('fill', AXIS_TEXT_COLOR)
      .style('font-size', '0.72rem')
      .style('font-family', CHART_FONT);

    yAxisGroup.selectAll('.domain, .tick line')
      .style('stroke', AXIS_TEXT_COLOR);

    yAxisGroup.append('text')
      .attr('transform', 'rotate(-90)')
      .attr('x', -height / 2)
      .attr('y', -42)
      .attr('fill', AXIS_TEXT_COLOR)
      .attr('text-anchor', 'middle')
      .attr('font-size', '0.78rem')
      .attr('font-weight', '600')
      .text('Rank');

    // Text wrapping utility
    const wrapText = (text: d3.Selection<SVGTextElement, any, any, any>, width: number) => {
      text.each(function () {
        const text = d3.select(this);
        let words = text.text().split(/\s+/).reverse();
        let word;
        let line: string[] = [];
        let lineNumber = 0;
        const lineHeight = 1.2;
        const y = text.attr('y');
        const x = text.attr('x') || 0;
        text.text(null);
        let tspan = text.append('tspan')
          .attr('x', x)
          .attr('y', y)
          .attr('dy', '0em');
        while ((word = words.pop())) {
          line.push(word);
          tspan.text(line.join(' '));
          if (tspan.node()?.getComputedTextLength()! > width) {
            line.pop();
            tspan.text(line.join(' '));
            line = [word];
            lineNumber++;
            tspan = text.append('tspan')
              .attr('x', x)
              .attr('y', y)
              .attr('dy', `${lineNumber * lineHeight}em`)
              .text(word);
          }
        }
      });
    };

    // Add metric names at the bottom
    g.selectAll('.metric-label')
      .data(rankColumns)
      .enter()
      .append('text')
      .attr('class', 'metric-label')
      .attr('x', d => xScale(d) || 0)
      .attr('y', height + 20)
      .attr('text-anchor', 'middle')
      .style('font-size', '0.72rem')
      .style('font-family', CHART_FONT)
      .style('font-weight', '500')
      .style('fill', AXIS_TEXT_COLOR)
      .text((_d, i) => numericColumns[i])
      .call(wrapText, 60);

    const legendY = height + 70;
    const legend = g.append('g')
      .attr('class', 'pcp-legend')
      .attr('transform', `translate(${width / 2 - 110}, ${legendY})`);

    // Square marker: trade-offs
    legend.append('rect')
      .attr('x', 0)
      .attr('y', -6)
      .attr('width', 10)
      .attr('height', 10)
      .attr('fill', '#c6ccd5')
      .attr('stroke', '#7f8b99')
      .attr('stroke-width', 1);

    legend.append('text')
      .attr('x', 16)
      .attr('y', 2)
      .style('font-size', '0.72rem')
      .style('font-family', CHART_FONT)
      .style('fill', AXIS_TEXT_COLOR)
      .text('Trade-offs');

    // Circle marker: specializers
    legend.append('circle')
      .attr('cx', 110)
      .attr('cy', -1)
      .attr('r', 5)
      .attr('fill', '#c6ccd5')
      .attr('stroke', '#7f8b99')
      .attr('stroke-width', 1);

    legend.append('text')
      .attr('x', 122)
      .attr('y', 2)
      .style('font-size', '0.72rem')
      .style('font-family', CHART_FONT)
      .style('fill', AXIS_TEXT_COLOR)
      .text('Specializers');
  };

  // Redraw chart on resize
  useEffect(() => {
    draw();

    const resizeObserver = new ResizeObserver(() => {
      draw();
    });

    if (containerRef.current) {
      resizeObserver.observe(containerRef.current);
    }

    return () => {
      if (containerRef.current) {
        resizeObserver.unobserve(containerRef.current);
      }
      // Clean up any existing tooltips
      d3.selectAll('.pcp-tooltip').remove();
    };
  }, [
    currentRanks,
    generalizerKey,
    specializationMatrix,
    tradeoffMatrix,
    solutionDetailsByKey,
    decisionKeys,
    objectiveKeys,
    hyperparameterKeys,
    inputParameterKeys,
    objectiveUnits,
    selectedSolutions,
    focusedSolution,
  ]);
  
  // Automatically fetch most generalized solution when component loads or dependencies change
  useEffect(() => {
    if (useCase && Object.keys(filters).length > 0 && Object.keys(weights).length > 0) {
      fetchMostGeneralizedSolution();
    }
  }, [useCase, JSON.stringify(filters), JSON.stringify(weights), selectedSolutions, focusedSolution, ranks]);
  
  // Automatically fetch and show most generalized solution
  const fetchMostGeneralizedSolution = async () => {
    if (!useCase) {
      console.warn('No use case provided for generalized solution API call');
      return;
    }
    
    try {
      const queryParams = new URLSearchParams();
      queryParams.append('use_case', useCase);
      
      // Add filters
      Object.entries(filters).forEach(([key, values]) =>
        values.forEach((filterValue) => queryParams.append(key, filterValue))
      );
      
      // Add weights
      Object.entries(weights).forEach(([key, weightValue]) =>
        queryParams.append(`weight_${key}`, weightValue.toString())
      );

      // Fetch enough rows so user-selected solutions can be highlighted in PCP.
      const requestedTopN = Math.max(
        PCP_GENERALIZER_COUNT,
        Object.keys(ranks || {}).length,
        selectedSolutions.length,
      );
      queryParams.append('top_n', requestedTopN.toString());
      
      const response = await fetch(`${API_BASE_URL}/api/generalizers?${queryParams.toString()}`);
      if (!response.ok) throw new Error('Failed to fetch most generalized solution data');
      
      const data = await response.json();
      console.log('Most generalized solution data received:', data);

      const key = data?.most_generalizer_rank_key
        ?? (data?.ranks ? Object.keys(data.ranks)[0] : undefined);
      setGeneralizerKey(key ?? null);
      setCurrentRanks(data.ranks || {});
      setSpecializationMatrix(data.specialization_matrix || {});
      setTradeoffMatrix(data.tradeoff_matrix || {});
      setSolutionDetailsByKey(data.solution_details_by_key || {});
      setDecisionKeys(data.decision_keys || []);
      setObjectiveKeys(data.objective_keys || []);
      setHyperparameterKeys(data.hyperparameter_keys || []);
      setInputParameterKeys(data.input_parameter_keys || []);
      setObjectiveUnits(data.objective_units || {});
      
    } catch (error) {
      console.error('Error fetching most generalized solution data:', error);
      setCurrentRanks(ranks || {});
      setSpecializationMatrix({});
      setTradeoffMatrix({});
      setSolutionDetailsByKey({});
      setDecisionKeys([]);
      setObjectiveKeys([]);
      setHyperparameterKeys([]);
      setInputParameterKeys([]);
      setObjectiveUnits({});
    }
  };

  // Styles inside the component
  const styles = {
    container: {
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      width: '100%',
      height: '100%',
      minHeight: 0,
      position: 'relative',
      overflow: 'hidden',
    },
    sliderContainer: {
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      gap: '4px'
    },
    chart: {
      flexGrow: 1,
      width: '100%',
      maxWidth: '600px',
      height: '100%',
      minHeight: 0,
      display: 'block',
    },
  };

  return (
    <Box ref={containerRef} sx={styles.container}>
      {/* Chart SVG */}
      <svg
        ref={ref}
        style={styles.chart}
      />
    </Box>
  );
};

export default ParallelCoordinatesChart;



