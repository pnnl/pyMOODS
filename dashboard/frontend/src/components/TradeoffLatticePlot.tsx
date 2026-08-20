import React, { useEffect, useMemo, useRef, useState } from "react";
import * as d3 from "d3";
import {
  Alert,
  Box,
  Checkbox,
  Chip,
  FormControlLabel,
  IconButton,
  LinearProgress,
  Tooltip,
  Typography,
} from "@mui/material";
import CropFreeIcon from "@mui/icons-material/CropFree";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import config from "../config";
import { useDashboardStore } from "../store/dashboardStore";

const { API_BASE_URL } = config;

interface TradeoffLatticePlotProps {
  useCase: string;
  filters: Record<string, string[]>;
  weights?: Record<string, number>;
}

interface LatticeNode {
  id: string;
  x: number;
  y: number;
  members: string[];
  label_lines: string[];
  objectives: Record<string, number>;
  decisions: Record<string, number>;
}

interface LatticeEdgeTest {
  key: string;
  direction: number | null;
  pvalue: number;
  magnitude: number | null;
}

interface LatticeEdge {
  source: string;
  target: string;
  tests: LatticeEdgeTest[];
}

interface LatticePayload {
  nodes: LatticeNode[];
  edges: LatticeEdge[];
  ovars: string[];
  dvars: string[];
  available_scenario_keys?: string[];
  selected_scenario_keys?: string[];
}

const SELECTION_COLORS = [
  "#D1495B",
  "#2A9D8F",
  "#F4A261",
  "#6C5CE7",
  "#3A86FF",
  "#E76F51",
];

type SimNode = d3.SimulationNodeDatum & {
  id: string;
  anchorX: number;
  anchorY: number;
  members: string[];
  labelLines: string[];
  objectives: Record<string, number>;
  radius: number;
  collisionRadius: number;
};

type SimLink = d3.SimulationLinkDatum<SimNode> & {
  source: string | SimNode;
  target: string | SimNode;
  label: string;
};

const EDGE_LABEL_ALPHA = 0.5;

const TradeoffLatticePlot: React.FC<TradeoffLatticePlotProps> = ({ useCase, filters, weights }) => {
  const { setAvailableScenarioKeys, setActiveScenarioKeys, dashboardState } = useDashboardStore();
  const storeScenarioKeys = dashboardState.activeScenarioKeys;

  const [data, setData] = useState<LatticePayload | null>(null);
  const [selectedScenarioKeys, setSelectedScenarioKeys] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const svgRef = useRef<SVGSVGElement | null>(null);
  const tooltipRef = useRef<HTMLDivElement | null>(null);
  const zoomBehaviorRef = useRef<d3.ZoomBehavior<SVGSVGElement, unknown> | null>(null);
  const selectedNodeIdsRef = useRef<Set<string>>(new Set());
  const selectedNodeColorsRef = useRef<Map<string, string>>(new Map());
  const resetTransformRef = useRef<d3.ZoomTransform>(d3.zoomIdentity);
  const currentTransformRef = useRef<d3.ZoomTransform>(d3.zoomIdentity);
  const availableScenarioKeys = data?.available_scenario_keys || [];

  // React state mirroring the D3-managed selection so the color legend re-renders.
  const [selectedNodeColors, setSelectedNodeColors] = useState<{ id: string; color: string }[]>([]);
  // Callable refs set inside the D3 effect so React buttons can trigger D3 actions.
  const fitRef = useRef<(animate: boolean) => void>(() => {});
  const clearSelectionRef = useRef<() => void>(() => {});
  // Suppresses the click event that fires after a drag operation.
  const isDraggingRef = useRef(false);

  // True when selectedScenarioKeys was just written by the API response handler.
  // The next effect run caused by that state change should skip the fetch to
  // avoid the circular double-load: mount → fetch → API sets keys → fetch again.
  const keysSetByApiRef = useRef(false);

  useEffect(() => {
    setSelectedScenarioKeys([]);
    setActiveScenarioKeys([]);
  }, [useCase]);

  // When the API returns available keys, publish them to the store so the
  // agent knows which values are valid for SET_AGGREGATION_LEVEL.
  useEffect(() => {
    if (availableScenarioKeys.length > 0) {
      setAvailableScenarioKeys(availableScenarioKeys);
    }
  }, [availableScenarioKeys]);

  // When the agent issues SET_AGGREGATION_LEVEL, apply it to local state.
  useEffect(() => {
    if (storeScenarioKeys.length > 0) {
      setSelectedScenarioKeys(storeScenarioKeys);
    }
  }, [storeScenarioKeys]);

  useEffect(() => {
    // Skip the refetch that would otherwise be triggered when the API response
    // itself updates selectedScenarioKeys (the data is already loaded).
    if (keysSetByApiRef.current) {
      keysSetByApiRef.current = false;
      return;
    }

    if (!useCase) {
      setData(null);
      setLoading(false);
      return;
    }

    const abortController = new AbortController();
    setLoading(true);
    setError(null);

    const queryParams = new URLSearchParams();
    queryParams.append("use_case", useCase);

    Object.entries(filters).forEach(([key, values]) => {
      values.forEach((value) => queryParams.append(key, value));
    });

    Object.entries(weights || {}).forEach(([key, value]) => {
      queryParams.append(`weight_${key}`, value.toString());
    });

    selectedScenarioKeys.forEach((key) => queryParams.append("scenario_key", key));

    fetch(`${API_BASE_URL}/api/tradeoff-lattice?${queryParams.toString()}`, { signal: abortController.signal })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error("Failed to load tradeoff lattice data.");
        }
        return response.json();
      })
      .then((jsonData: LatticePayload) => {
        setData(jsonData);
        if (jsonData.selected_scenario_keys) {
          const nextKeys = jsonData.selected_scenario_keys;
          if (nextKeys.join("|") !== selectedScenarioKeys.join("|")) {
            keysSetByApiRef.current = true;
            setSelectedScenarioKeys(nextKeys);
          }
        }
      })
      .catch((fetchError) => {
        if (fetchError.name === "AbortError") return;
        console.error("Error loading tradeoff lattice artifact:", fetchError);
        setError(fetchError instanceof Error ? fetchError.message : "Failed to load tradeoff lattice.");
      })
      .finally(() => {
        if (!abortController.signal.aborted) setLoading(false);
      });

    return () => abortController.abort();
  }, [filters, selectedScenarioKeys, useCase, weights]);

  const graph = useMemo(() => {
    if (!data) {
      return null;
    }

    const nodes: SimNode[] = data.nodes.map((node) => {
      const radius = Math.max(20, Math.min(38, 18 + Math.sqrt(node.members.length) * 2.5));
      return {
        id: node.id,
        anchorX: node.x,
        anchorY: node.y,
        members: node.members,
        labelLines: node.label_lines,
        objectives: node.objectives,
        // Scale radius with member count so larger groups are visually larger.
        radius,
        collisionRadius: Math.max(
          60,
          radius + Math.max(...node.label_lines.map((line) => line.length), 0) * 3.2,
        ),
      };
    });

    const links: SimLink[] = data.edges.map((edge) => ({
      source: edge.source,
      target: edge.target,
      label: edge.tests
        .filter((test) => test.pvalue <= EDGE_LABEL_ALPHA)
        .map((test) => `${(test.direction ?? 0) > 0 ? "+" : "-"} ${test.key}`)
        .join("\n"),
    }));

    return { nodes, links };
  }, [data]);

  useEffect(() => {
    if (!graph || !svgRef.current || !containerRef.current || !tooltipRef.current) {
      return;
    }

    const container = containerRef.current;
    const svg = d3.select(svgRef.current);
    const tooltip = d3.select(tooltipRef.current);
    svg.selectAll("*").remove();

    // Clear any selection from the previous graph so stale node IDs don't
    // carry over and appear highlighted in the newly rendered graph.
    selectedNodeIdsRef.current.clear();
    selectedNodeColorsRef.current.clear();
    setSelectedNodeColors([]);

    const { width: rawWidth, height: rawHeight } = container.getBoundingClientRect();
    const width = Math.max(rawWidth, 640);
    const height = Math.max(rawHeight, 640);

    svg.attr("viewBox", `0 0 ${width} ${height}`);

    const xExtent = d3.extent(graph.nodes, (node) => node.anchorX) as [number, number];
    const yExtent = d3.extent(graph.nodes, (node) => node.anchorY) as [number, number];
    const xScale = d3.scaleLinear().domain(xExtent).range([72, width - 72]);
    const yScale = d3.scaleLinear().domain(yExtent).range([56, height - 56]);

    graph.nodes.forEach((node) => {
      node.x = xScale(node.anchorX);
      node.y = yScale(node.anchorY);
      node.anchorX = xScale(node.anchorX);
      node.anchorY = yScale(node.anchorY);
    });

    const defs = svg.append("defs");
    defs
      .append("filter")
      .attr("id", "node-glow")
      .append("feDropShadow")
      .attr("dx", 0)
      .attr("dy", 4)
      .attr("stdDeviation", 5)
      .attr("flood-color", "rgba(72, 113, 153, 0.22)");

    defs
      .append("marker")
      .attr("id", "tradeoff-arrow")
      .attr("viewBox", "0 -5 10 10")
      .attr("refX", 10) // tip of the arrowhead aligns with the line endpoint
      .attr("refY", 0)
      .attr("markerWidth", 7)
      .attr("markerHeight", 7)
      .attr("orient", "auto")
      .append("path")
      .attr("d", "M0,-5L10,0L0,5")
      .attr("fill", "rgba(120,120,120,0.6)");

    const root = svg.append("g");
    const zoom = d3.zoom<SVGSVGElement, unknown>().scaleExtent([0.6, 3.5]).on("zoom", (event) => {
      currentTransformRef.current = event.transform;
      root.attr("transform", event.transform.toString());
    });
    zoomBehaviorRef.current = zoom;
    svg.call(zoom);
    svg.on("dblclick.zoom", null);

    const interactionLayer = svg.append("g");
    const selectionBox = interactionLayer
      .append("rect")
      .attr("fill", "rgba(92,141,184,0.12)")
      .attr("stroke", "rgba(92,141,184,0.9)")
      .attr("stroke-width", 1.5)
      .attr("stroke-dasharray", "6 4")
      .style("display", "none");

    const link = root
      .append("g")
      .selectAll("g")
      .data(graph.links)
      .enter()
      .append("g");

    const linkFirstHalf = link
      .append("line")
      .attr("stroke", "rgba(140,140,140,0.45)")
      .attr("stroke-width", 1.75)
      .attr("stroke-linecap", "round");

    const linkSecondHalf = link
      .append("line")
      .attr("stroke", "rgba(140,140,140,0.45)")
      .attr("stroke-width", 1.75)
      .attr("stroke-linecap", "round")
      .attr("marker-end", "url(#tradeoff-arrow)");

    const edgeLabel = root
      .append("g")
      .selectAll("text")
      .data(graph.links.filter((item) => item.label))
      .enter()
      .append("text")
      .attr("font-size", 13)
      .attr("fill", "#52606d")
      .attr("text-anchor", "middle")
      .attr("dominant-baseline", "middle")
      .style("pointer-events", "none")
      .attr("paint-order", "stroke")
      .attr("stroke", "rgba(247,251,255,0.96)")
      .attr("stroke-width", 7)
      .each(function (d) {
        const text = d3.select(this);
        const lines = d.label.split("\n");
        d.label.split("\n").forEach((line, index) => {
          text
            .append("tspan")
            .attr("x", 0)
            .attr("dy", index === 0 ? `${-((lines.length - 1) * 6)}px` : "13px")
            .text(line);
        });
      });

    const node = root
      .append("g")
      .selectAll("g")
      .data(graph.nodes)
      .enter()
      .append("g")
      .style("cursor", "pointer")
      .call(
        d3
          .drag<SVGGElement, SimNode>()
          .on("start", (event, d) => {
            isDraggingRef.current = false;
            if (!event.active) {
              simulation.alphaTarget(0.2).restart();
            }
            d.fx = d.x;
            d.fy = d.y;
          })
          .on("drag", (event, d) => {
            isDraggingRef.current = true;
            d.fx = event.x;
            d.fy = event.y;
          })
          .on("end", (event, d) => {
            if (!event.active) {
              simulation.alphaTarget(0);
            }
            d.fx = event.x;
            d.fy = event.y;
          }),
      );

    node
      .append("circle")
      .attr("class", "outer-ring")
      .attr("r", (d) => d.radius)
      .attr("fill", "rgba(255,255,255,0)")
      .attr("stroke", "#5C8DB8")
      .attr("stroke-width", 4.5)
      .attr("filter", "url(#node-glow)");

    node
      .append("circle")
      .attr("class", "inner-ring")
      .attr("r", (d) => d.radius - 7)
      .attr("fill", "rgba(92,141,184,0.08)")
      .attr("stroke", "rgba(92,141,184,0.18)")
      .attr("stroke-width", 1.5);

    // Render label lines centered inside each node. Two lines are vertically
    // centered together; a single line sits at the node's midpoint.
    node.each(function (d) {
      const lines = [d.labelLines[0] || d.id, d.labelLines[1]].filter(Boolean);
      const lineHeight = 15;
      const totalHeight = (lines.length - 1) * lineHeight;
      lines.forEach((line, i) => {
        d3.select(this)
          .append("text")
          .attr("text-anchor", "middle")
          .attr("y", -totalHeight / 2 + i * lineHeight)
          .attr("dy", "0.35em")
          .attr("font-size", i === 0 ? 15 : 12)
          .attr("font-weight", i === 0 ? 700 : 500)
          .attr("fill", i === 0 ? "#111111" : "#52606d")
          .attr("paint-order", "stroke")
          .attr("stroke", "rgba(247,251,255,0.98)")
          .attr("stroke-width", i === 0 ? 6 : 5)
          .style("pointer-events", "none")
          .text(line);
      });
    });

    const getLinkNodeId = (value: string | SimNode) => (typeof value === "string" ? value : value.id);
    const getNodeColor = (nodeId: string) => selectedNodeColorsRef.current.get(nodeId) || "#5C8DB8";
    const getInnerFill = (nodeId: string) => {
      const selectedColor = selectedNodeColorsRef.current.get(nodeId);
      if (!selectedColor) {
        return "rgba(92,141,184,0.08)";
      }
      const color = d3.color(selectedColor);
      return color?.copy({ opacity: 0.12 }).formatRgb() || "rgba(92,141,184,0.12)";
    };

    const clamp = (value: number, min: number, max: number) => Math.max(min, Math.min(max, value));

    const fitGraphToViewport = (animate: boolean) => {
      if (!svgRef.current || !zoomBehaviorRef.current) {
        return;
      }

      const xMin = d3.min(graph.nodes, (node) => (node.x ?? node.anchorX) - node.collisionRadius);
      const xMax = d3.max(graph.nodes, (node) => (node.x ?? node.anchorX) + node.collisionRadius);
      const yMin = d3.min(graph.nodes, (node) => (node.y ?? node.anchorY) - node.collisionRadius);
      const yMax = d3.max(graph.nodes, (node) => (node.y ?? node.anchorY) + node.collisionRadius);

      if (
        xMin === undefined ||
        xMax === undefined ||
        yMin === undefined ||
        yMax === undefined ||
        xMax - xMin <= 0 ||
        yMax - yMin <= 0
      ) {
        return;
      }

      const bounds = {
        x: xMin,
        y: yMin,
        width: xMax - xMin,
        height: yMax - yMin,
      };

      const padding = 40;
      const availableWidth = width - padding * 2;
      const availableHeight = height - padding * 2;
      const scale = Math.min(
        1.35,
        Math.max(
          0.9,
          Math.min(availableWidth / bounds.width, availableHeight / bounds.height),
        ),
      );

      const tx = width / 2 - scale * (bounds.x + bounds.width / 2);
      const ty = height / 2 - scale * (bounds.y + bounds.height / 2);
      const transform = d3.zoomIdentity.translate(tx, ty).scale(scale);
      resetTransformRef.current = transform;

      const selection = d3.select(svgRef.current);
      const action = animate ? selection.transition().duration(260) : selection;
      action.call(zoomBehaviorRef.current.transform, transform);
    };

    fitRef.current = fitGraphToViewport;

    const startBoxZoom = (event: MouseEvent) => {
      if (!svgRef.current || !zoomBehaviorRef.current) {
        return;
      }

      const [startX, startY] = d3.pointer(event, svgRef.current);
      selectionBox
        .style("display", null)
        .attr("x", startX)
        .attr("y", startY)
        .attr("width", 0)
        .attr("height", 0);

      const onMouseMove = (moveEvent: MouseEvent) => {
        if (!svgRef.current) {
          return;
        }

        const [currentX, currentY] = d3.pointer(moveEvent, svgRef.current);
        const x = Math.min(startX, currentX);
        const y = Math.min(startY, currentY);
        const boxWidth = Math.abs(currentX - startX);
        const boxHeight = Math.abs(currentY - startY);

        selectionBox
          .attr("x", x)
          .attr("y", y)
          .attr("width", boxWidth)
          .attr("height", boxHeight);
      };

      const onMouseUp = (upEvent: MouseEvent) => {
        window.removeEventListener("mousemove", onMouseMove);
        window.removeEventListener("mouseup", onMouseUp);

        if (!svgRef.current || !zoomBehaviorRef.current) {
          return;
        }

        const [endX, endY] = d3.pointer(upEvent, svgRef.current);
        selectionBox.style("display", "none");

        const x = Math.min(startX, endX);
        const y = Math.min(startY, endY);
        const boxWidth = Math.abs(endX - startX);
        const boxHeight = Math.abs(endY - startY);

        if (boxWidth < 24 || boxHeight < 24) {
          return;
        }

        const current = currentTransformRef.current;
        const centerX = x + boxWidth / 2;
        const centerY = y + boxHeight / 2;
        const worldCenterX = current.invertX(centerX);
        const worldCenterY = current.invertY(centerY);
        const nextScale = clamp(
          current.k * Math.min(width / boxWidth, height / boxHeight),
          0.6,
          3.5,
        );

        const nextTransform = d3.zoomIdentity
          .translate(width / 2, height / 2)
          .scale(nextScale)
          .translate(-worldCenterX, -worldCenterY);

        resetTransformRef.current = nextTransform;
        d3.select(svgRef.current)
          .transition()
          .duration(260)
          .call(zoomBehaviorRef.current.transform, nextTransform);
      };

      window.addEventListener("mousemove", onMouseMove);
      window.addEventListener("mouseup", onMouseUp);
    };

    const applyHighlight = (focusIds?: Set<string>) => {
      const selectedIds = selectedNodeIdsRef.current;
      const activeIds = focusIds ?? (selectedIds.size ? new Set(selectedIds) : null);

      if (!activeIds || activeIds.size === 0) {
        node.transition().duration(180).style("opacity", 1);
        node
          .selectAll<SVGCircleElement, SimNode>("circle.outer-ring")
          .transition()
          .duration(180)
          .attr("stroke", "#5C8DB8")
          .attr("stroke-width", 4.5);
        node
          .selectAll<SVGCircleElement, SimNode>("circle.inner-ring")
          .transition()
          .duration(180)
          .attr("fill", "rgba(92,141,184,0.08)")
          .attr("stroke", "rgba(92,141,184,0.18)")
          .attr("stroke-width", 1.5);
        linkFirstHalf
          .transition()
          .duration(180)
          .attr("stroke", "rgba(140,140,140,0.45)")
          .attr("stroke-width", 2);
        linkSecondHalf
          .transition()
          .duration(180)
          .attr("stroke", "rgba(140,140,140,0.45)")
          .attr("stroke-width", 2);
        edgeLabel.transition().duration(180).style("opacity", 1);
        return;
      }

      node
        .transition()
        .duration(180)
        .style("opacity", (nodeDatum) => (activeIds.has(nodeDatum.id) ? 1 : 0.22));

      node
        .selectAll<SVGCircleElement, SimNode>("circle.outer-ring")
        .transition()
        .duration(180)
        .attr("stroke", function () {
          const parentDatum = d3.select(this.parentNode as SVGGElement).datum() as SimNode;
          return activeIds.has(parentDatum.id) ? getNodeColor(parentDatum.id) : "#5C8DB8";
        })
        .attr("stroke-width", function () {
          const parentDatum = d3.select(this.parentNode as SVGGElement).datum() as SimNode;
          return activeIds.has(parentDatum.id) ? 6 : 4.5;
        });

      node
        .selectAll<SVGCircleElement, SimNode>("circle.inner-ring")
        .transition()
        .duration(180)
        .attr("fill", function () {
          const parentDatum = d3.select(this.parentNode as SVGGElement).datum() as SimNode;
          return getInnerFill(parentDatum.id);
        })
        .attr("stroke", function () {
          const parentDatum = d3.select(this.parentNode as SVGGElement).datum() as SimNode;
          const color = d3.color(getNodeColor(parentDatum.id));
          return selectedNodeColorsRef.current.has(parentDatum.id)
            ? color?.copy({ opacity: 0.24 }).formatRgb() || "rgba(92,141,184,0.24)"
            : "rgba(92,141,184,0.18)";
        })
        .attr("stroke-width", function () {
          const parentDatum = d3.select(this.parentNode as SVGGElement).datum() as SimNode;
          return activeIds.has(parentDatum.id) ? 2.5 : 1.5;
        });

      linkFirstHalf
        .transition()
        .duration(180)
        .attr("stroke", (edgeDatum) => {
          const sourceId = getLinkNodeId(edgeDatum.source);
          const targetId = getLinkNodeId(edgeDatum.target);
          if (activeIds.has(sourceId) && activeIds.has(targetId)) return getNodeColor(sourceId);
          if (activeIds.has(sourceId)) return getNodeColor(sourceId);
          if (activeIds.has(targetId)) return getNodeColor(targetId);
          return "rgba(140,140,140,0.12)";
        })
        .attr("stroke-width", (edgeDatum) => {
          const sourceId = getLinkNodeId(edgeDatum.source);
          const targetId = getLinkNodeId(edgeDatum.target);
          return activeIds.has(sourceId) || activeIds.has(targetId) ? 3.5 : 1.5;
        });

      linkSecondHalf
        .transition()
        .duration(180)
        .attr("stroke", (edgeDatum) => {
          const sourceId = getLinkNodeId(edgeDatum.source);
          const targetId = getLinkNodeId(edgeDatum.target);
          if (activeIds.has(sourceId) && activeIds.has(targetId)) return getNodeColor(targetId);
          if (activeIds.has(targetId)) return getNodeColor(targetId);
          if (activeIds.has(sourceId)) return getNodeColor(sourceId);
          return "rgba(140,140,140,0.12)";
        })
        .attr("stroke-width", (edgeDatum) => {
          const sourceId = getLinkNodeId(edgeDatum.source);
          const targetId = getLinkNodeId(edgeDatum.target);
          return activeIds.has(sourceId) || activeIds.has(targetId) ? 3.5 : 1.5;
        });

      edgeLabel
        .transition()
        .duration(180)
        .style("opacity", (edgeDatum) => {
          const sourceId = getLinkNodeId(edgeDatum.source);
          const targetId = getLinkNodeId(edgeDatum.target);
          return activeIds.has(sourceId) || activeIds.has(targetId) ? 1 : 0.15;
        });
    };

    node
      .on("mouseenter", (event: MouseEvent, d) => {
        const connectedIds = new Set<string>(selectedNodeIdsRef.current);
        connectedIds.add(d.id);
        graph.links.forEach((edge) => {
          const sourceId = getLinkNodeId(edge.source);
          const targetId = getLinkNodeId(edge.target);
          if (connectedIds.has(sourceId) || connectedIds.has(targetId) || sourceId === d.id || targetId === d.id) {
            connectedIds.add(sourceId);
            connectedIds.add(targetId);
          }
        });
        applyHighlight(connectedIds);

        const extraLines = d.labelLines.slice(2).filter(Boolean);
        const objEntries = Object.entries(d.objectives || {});
        const memberLine = `<div style="color:#52606d;font-size:11px;margin-bottom:4px">${d.members.length} solution${d.members.length !== 1 ? "s" : ""}</div>`;
        const extraHtml = extraLines.length ? `<div style="margin-bottom:5px">${extraLines.join("<br>")}</div>` : "";
        const objHtml = objEntries.length
          ? `<div style="margin-top:5px;padding-top:5px;border-top:1px solid rgba(0,0,0,0.08)">${objEntries.map(([k, v]) => `<span style="color:#52606d;font-size:11px">${k}:</span> <b>${typeof v === "number" ? v.toFixed(3) : v}</b>`).join("<br>")}</div>`
          : "";

        const placeTooltip = (ev: MouseEvent) => {
          const el = tooltipRef.current;
          if (!el) return;
          const { width: tw, height: th } = el.getBoundingClientRect();
          const left = Math.min(ev.clientX + 12, window.innerWidth - tw - 8);
          const top = Math.max(8, Math.min(ev.clientY - 12, window.innerHeight - th - 8));
          tooltip.style("left", `${left}px`).style("top", `${top}px`);
        };

        tooltip.style("opacity", 1).html(memberLine + extraHtml + objHtml);
        placeTooltip(event);
      })
      .on("mousemove", (event: MouseEvent) => {
        const el = tooltipRef.current;
        if (!el) return;
        const { width: tw, height: th } = el.getBoundingClientRect();
        const left = Math.min(event.clientX + 12, window.innerWidth - tw - 8);
        const top = Math.max(8, Math.min(event.clientY - 12, window.innerHeight - th - 8));
        tooltip.style("left", `${left}px`).style("top", `${top}px`);
      })
      .on("mouseleave", () => {
        applyHighlight();
        tooltip.style("opacity", 0);
      })
      .on("click", (_event, d) => {
        if (isDraggingRef.current) {
          isDraggingRef.current = false;
          return;
        }
        const selectedIds = selectedNodeIdsRef.current;
        if (selectedIds.has(d.id)) {
          selectedIds.delete(d.id);
          selectedNodeColorsRef.current.delete(d.id);
        } else {
          selectedIds.add(d.id);
          const usedColors = new Set(selectedNodeColorsRef.current.values());
          const nextColor =
            SELECTION_COLORS.find((color) => !usedColors.has(color)) ||
            SELECTION_COLORS[selectedNodeColorsRef.current.size % SELECTION_COLORS.length];
          selectedNodeColorsRef.current.set(d.id, nextColor);
        }
        applyHighlight();
        setSelectedNodeColors(
          Array.from(selectedNodeColorsRef.current.entries()).map(([id, color]) => ({ id, color })),
        );
      })
      .on("dblclick", (event) => {
        event.stopPropagation();
        selectedNodeIdsRef.current.clear();
        selectedNodeColorsRef.current.clear();
        applyHighlight();
        tooltip.style("opacity", 0);
        setSelectedNodeColors([]);
      });

    clearSelectionRef.current = () => {
      selectedNodeIdsRef.current.clear();
      selectedNodeColorsRef.current.clear();
      applyHighlight();
      tooltip.style("opacity", 0);
      setSelectedNodeColors([]);
    };

    // Scale force parameters with node count so the layout stays readable
    // for both small graphs (2–3 nodes) and larger ones (15+ nodes).
    const n = graph.nodes.length;
    const linkDistance = Math.max(120, 320 / Math.sqrt(Math.max(1, n - 1)));
    const chargeStrength = -Math.max(200, 600 / Math.sqrt(Math.max(1, n)));

    const simulation = d3
      .forceSimulation(graph.nodes)
      .force(
        "link",
        d3
          .forceLink<SimNode, SimLink>(graph.links)
          .id((d) => d.id)
          .distance(linkDistance)
          .strength(0.22),
      )
      .force("charge", d3.forceManyBody().strength(chargeStrength))
      .force("collide", d3.forceCollide<SimNode>().radius((d) => d.collisionRadius).strength(1))
      .force("x", d3.forceX<SimNode>((d) => d.anchorX).strength(0.06))
      .force("y", d3.forceY<SimNode>((d) => d.anchorY).strength(0.2))
      .force("center", d3.forceCenter(width / 2, height / 2).strength(0.03))
      .alpha(1)
      .alphaDecay(0.045)
      .velocityDecay(0.38);

    simulation.on("tick", () => {
      linkFirstHalf
        .attr("x1", (d) => (d.source as SimNode).x ?? 0)
        .attr("y1", (d) => (d.source as SimNode).y ?? 0)
        .attr("x2", (d) => (((d.source as SimNode).x ?? 0) + ((d.target as SimNode).x ?? 0)) / 2)
        .attr("y2", (d) => (((d.source as SimNode).y ?? 0) + ((d.target as SimNode).y ?? 0)) / 2);

      linkSecondHalf
        .attr("x1", (d) => (((d.source as SimNode).x ?? 0) + ((d.target as SimNode).x ?? 0)) / 2)
        .attr("y1", (d) => (((d.source as SimNode).y ?? 0) + ((d.target as SimNode).y ?? 0)) / 2)
        .attr("x2", (d) => {
          const t = d.target as SimNode;
          const tx = t.x ?? 0, ty = t.y ?? 0;
          const mx = (((d.source as SimNode).x ?? 0) + tx) / 2;
          const my = (((d.source as SimNode).y ?? 0) + ty) / 2;
          const dx = tx - mx, dy = ty - my;
          const dist = Math.sqrt(dx * dx + dy * dy);
          const stop = t.radius + 4; // 4px gap so the arrowhead doesn't clip the stroke
          return dist > stop ? tx - (dx / dist) * stop : mx;
        })
        .attr("y2", (d) => {
          const t = d.target as SimNode;
          const tx = t.x ?? 0, ty = t.y ?? 0;
          const mx = (((d.source as SimNode).x ?? 0) + tx) / 2;
          const my = (((d.source as SimNode).y ?? 0) + ty) / 2;
          const dx = tx - mx, dy = ty - my;
          const dist = Math.sqrt(dx * dx + dy * dy);
          const stop = t.radius + 4;
          return dist > stop ? ty - (dy / dist) * stop : my;
        });

      edgeLabel
        .attr(
          "transform",
          (d) =>
            `translate(${(((d.source as SimNode).x ?? 0) + ((d.target as SimNode).x ?? 0)) / 2},${((((d.source as SimNode).y ?? 0) + ((d.target as SimNode).y ?? 0)) / 2) - 6})`,
        );

      node.attr("transform", (d) => `translate(${d.x ?? 0},${d.y ?? 0})`);
    });

    fitGraphToViewport(false);

    svg.on("mousedown.boxzoom", (event: MouseEvent) => {
      if (!event.shiftKey || event.button !== 0) {
        return;
      }

      event.preventDefault();
      event.stopPropagation();
      startBoxZoom(event);
    });

    simulation.on("end", () => {
      const current = currentTransformRef.current;
      const reset = resetTransformRef.current;
      const transformUnchanged =
        Math.abs(current.x - reset.x) < 1 &&
        Math.abs(current.y - reset.y) < 1 &&
        Math.abs(current.k - reset.k) < 0.01;

      if (transformUnchanged) {
        fitGraphToViewport(false);
      }
    });

    return () => {
      svg.on("mousedown.boxzoom", null);
      simulation.stop();
    };
  }, [graph]);

  // No data and not loading — truly empty state.
  if (!data && !loading) {
    return (
      <Box sx={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%" }}>
        <Typography color="text.secondary">No tradeoff lattice data available.</Typography>
      </Box>
    );
  }

  const interactionHints = useMemo(() => (
    <Box sx={{ p: 0.5, maxWidth: 220 }}>
      <Typography variant="caption" sx={{ fontWeight: 700, display: "block", mb: 0.5 }}>Interactions</Typography>
      {[
        ["Click node", "Select / deselect"],
        ["Drag node", "Reposition"],
        ["Scroll", "Zoom in / out"],
        ["Click + drag canvas", "Pan"],
        ["Shift + drag canvas", "Box zoom"],
        ["Double-click node", "Clear all selections"],
      ].map(([key, val]) => (
        <Box key={key} sx={{ display: "flex", justifyContent: "space-between", gap: 1.5, mb: 0.25 }}>
          <Typography variant="caption" sx={{ color: "text.secondary" }}>{key}</Typography>
          <Typography variant="caption" sx={{ fontWeight: 600 }}>{val}</Typography>
        </Box>
      ))}
      <Box sx={{ mt: 1, pt: 0.75, borderTop: "1px solid rgba(0,0,0,0.08)" }}>
        <Typography variant="caption" sx={{ fontWeight: 700, display: "block", mb: 0.25 }}>Edge labels</Typography>
        <Typography variant="caption" sx={{ color: "text.secondary", display: "block" }}>
          Arrow points toward the <b>dominated</b> group.
        </Typography>
        <Typography variant="caption" sx={{ color: "text.secondary", display: "block" }}>
          <b>+</b> / <b>−</b> = objective improves / worsens (p ≤ 0.5).
        </Typography>
      </Box>
    </Box>
  ), []);

  return (
    <Box sx={{ width: "100%", height: "100%", minHeight: 0, flex: 1, display: "flex", flexDirection: "column" }}>
      {loading && <LinearProgress sx={{ flexShrink: 0, height: 2 }} />}
      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ flexShrink: 0, borderRadius: 0 }}>
          {error}
        </Alert>
      )}

      {/* Aggregation controls — styled to match the ScatterPlot axis toolbar */}
      {availableScenarioKeys.length > 0 && (
        <Box sx={{ px: 1.5, pt: 1, pb: 0.5, flexShrink: 0 }}>
          <Box
            sx={{
              display: "flex",
              alignItems: "center",
              flexWrap: "wrap",
              gap: 0.5,
              background: "rgba(27,41,59,0.04)",
              border: "1px solid rgba(27,41,59,0.10)",
              borderRadius: "8px",
              px: 1.5,
              py: 0.75,
            }}
          >
            <Typography variant="body2" sx={{ color: "text.secondary", fontWeight: 600, mr: 0.5, whiteSpace: "nowrap" }}>
              Group by:
            </Typography>
            {availableScenarioKeys.map((key) => {
              const isLastChecked = selectedScenarioKeys.includes(key) && selectedScenarioKeys.length === 1;
              return (
                <Tooltip
                  key={key}
                  title={isLastChecked ? "At least one grouping attribute must be selected." : ""}
                  placement="top"
                  arrow
                >
                  <FormControlLabel
                    control={
                      <Checkbox
                        size="small"
                        checked={selectedScenarioKeys.includes(key)}
                        disabled={isLastChecked}
                        onChange={(event) => {
                          setSelectedScenarioKeys((current) =>
                            event.target.checked
                              ? [...current, key]
                              : current.filter((item) => item !== key),
                          );
                        }}
                      />
                    }
                    label={key}
                    sx={{ mr: 0.5, ml: 0, ".MuiFormControlLabel-label": { fontSize: "0.875rem" } }}
                  />
                </Tooltip>
              );
            })}
            <Box sx={{ ml: "auto" }}>
              <Tooltip title={interactionHints} placement="bottom-end" arrow>
                <IconButton size="small" sx={{ color: "text.secondary" }}>
                  <InfoOutlinedIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            </Box>
          </Box>
        </Box>
      )}

      {/* Canvas */}
      <Box ref={containerRef} sx={{ flex: 1, minHeight: 0, position: "relative" }}>
        <Box
          ref={tooltipRef}
          sx={{
            position: "fixed",
            pointerEvents: "none",
            opacity: 0,
            maxWidth: 280,
            px: 1.5,
            py: 1,
            borderRadius: 2,
            bgcolor: "rgba(255,255,255,0.97)",
            border: "1px solid rgba(92,141,184,0.18)",
            color: "#111111",
            fontSize: 12,
            lineHeight: 1.35,
            textAlign: "left",
            whiteSpace: "normal",
            boxShadow: "0 12px 30px rgba(32, 54, 76, 0.14)",
            backdropFilter: "blur(10px)",
            zIndex: 20,
          }}
        />
        <svg ref={svgRef} style={{ width: "100%", height: "100%", display: "block" }} />

        {/* Placeholder shown while the first fetch is in flight and no graph exists yet */}
        {!data && loading && (
          <Box sx={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 1, pointerEvents: "none" }}>
            <Typography variant="body2" color="text.secondary">Preparing graph…</Typography>
          </Box>
        )}

        {/* Fit-to-screen button */}
        <Tooltip title="Fit graph to screen" placement="left">
          <IconButton
            size="small"
            onClick={() => fitRef.current(true)}
            sx={{
              position: "absolute",
              bottom: 12,
              right: 12,
              bgcolor: "rgba(255,255,255,0.92)",
              border: "1px solid",
              borderColor: "divider",
              boxShadow: 1,
              "&:hover": { bgcolor: "rgba(255,255,255,1)" },
            }}
          >
            <CropFreeIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      </Box>

      {/* Selected-node color legend */}
      {selectedNodeColors.length > 0 && (
        <Box
          sx={{
            px: 2,
            py: 1,
            borderTop: "1px solid",
            borderColor: "divider",
            display: "flex",
            flexWrap: "wrap",
            alignItems: "center",
            gap: 0.75,
            flexShrink: 0,
          }}
        >
          <Typography variant="caption" color="text.secondary" sx={{ mr: 0.5 }}>
            Selected:
          </Typography>
          {selectedNodeColors.map(({ id, color }) => (
            <Chip
              key={id}
              label={id}
              size="small"
              sx={{
                bgcolor: color,
                color: "#fff",
                fontWeight: 600,
                fontSize: "0.75rem",
                height: 22,
              }}
            />
          ))}
          <Typography
            variant="caption"
            onClick={() => clearSelectionRef.current()}
            sx={{
              ml: "auto",
              color: "text.secondary",
              cursor: "pointer",
              textDecoration: "underline",
              "&:hover": { color: "text.primary" },
            }}
          >
            Clear selection
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default TradeoffLatticePlot;
