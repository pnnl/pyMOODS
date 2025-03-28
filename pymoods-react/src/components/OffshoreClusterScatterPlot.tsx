import { useState, useEffect } from 'react';
import * as Plotly from "plotly.js-basic-dist";
import createPlotlyComponent from "react-plotly.js/factory";
import * as Papa from 'papaparse';
import * as d3 from 'd3';
import Box from '@mui/material/Box';

const Plot = createPlotlyComponent(Plotly);

const CSV_FILES = [
    { path: '/data/COTTONWOOD_2018.csv', label: 'COTTONWOOD', color: 'blue' },
    { path: '/data/JOHNDAY_2018.csv', label: 'JOHNDAY', color: 'orange' },
    { path: '/data/MOSSLAND_2018.csv', label: 'MOSSLAND', color: 'green' },
    { path: '/data/TESLA_2018.csv', label: 'TESLA', color: 'red' },
    { path: '/data/WCASCADE_2018.csv', label: 'WCASCADE', color: 'purple' },
];

interface CsvRow {
    Year: number;
    Month: number;
    Day: number;
    Hour: number;
    Minute: number;
    windSpeed100m: number;
    windDirection100m: number;
    windSpeed140m: number;
    site?: string;
}

const OffshoreClusterScatterPlot: React.FC = () => {
    const [data, setData] = useState<CsvRow[]>([]);
    const [hullData, setHullData] = useState<Record<string, [number, number][]> | null>(null);
    
    useEffect(() => {
        const fetchData = async () => {
          let allData: CsvRow[] = [];
    
          for (const file of CSV_FILES) {
            const response = await fetch(file.path);
            const csvText = await response.text();
    
            Papa.parse(csvText, {
                skipEmptyLines: true,
                dynamicTyping: true,
                complete: (results) => {
                const rawRows = results.data as string[][];

                // Find header row
                const headerRowIndex = rawRows.findIndex((row) => row[0] === 'Year');
                    if (headerRowIndex === -1) return;

                    const validData = rawRows.slice(headerRowIndex + 1);

                    const parsedData: CsvRow[] = validData.map((row) => ({
                        Year: Number(row[0]),
                        Month: Number(row[1]),
                        Day: Number(row[2]),
                        Hour: Number(row[3]),
                        Minute: Number(row[4]),
                        windSpeed100m: Number(row[5]),
                        windDirection100m: Number(row[6]),
                        windSpeed140m: Number(row[7]),
                        site: file.label, // Assign site label
                    }));

                    allData = [...allData, ...parsedData];

                    // Only update state after processing all files
                    if (file === CSV_FILES[CSV_FILES.length - 1]) {
                        setData(allData);
                        computeConvexHulls(allData);
                    }
                },
            });
          }
        };
    
        fetchData();
    }, []);

    // Function to compute convex hulls using D3.js
    const computeConvexHulls = (allData: CsvRow[]) => {
        const hulls: Record<string, [number, number][]> = {};

        CSV_FILES.forEach((file) => {
        const points = allData
            .filter((row) => row.site === file.label)
            .map((row) => [row.windSpeed100m, row.windDirection100m] as [number, number]);

        const hull = d3.polygonHull(points);
        if (hull) {
            hulls[file.label] = hull;
        }
        });

        setHullData(hulls);
    };

    const plotData = (): Partial<Plotly.Data>[] => {
        if (data.length === 0) return [];

        const scatterData = CSV_FILES.map((file) => ({
            x: data.filter((row) => row.site === file.label).map((row) => row.windSpeed100m),
            y: data.filter((row) => row.site === file.label).map((row) => row.windDirection100m),
            mode: 'markers',
            type: 'scatter',
            marker: { size: 6, color: file.color },
            name: file.label,
        }));

        const hullTraces =
            hullData &&
            Object.entries(hullData).map(([site, hull]) => ({
                x: [...hull.map((p) => p[0]), hull[0][0]], // Close the polygon
                y: [...hull.map((p) => p[1]), hull[0][1]], // Close the polygon
                mode: 'lines',
                line: { color: CSV_FILES.find((f) => f.label === site)?.color, width: 2 },
                name: `${site} Hull`,
                showlegend: false,
            }));

        // Find the min and max values for both x and y axes
        const xValues = data.map((row) => row.windSpeed100m);
        const yValues = data.map((row) => row.windDirection100m);

        const xMin = Math.min(...xValues);
        const xMax = Math.max(...xValues);
        const yMin = Math.min(...yValues);
        const yMax = Math.max(...yValues);

        // Add some padding to the axes to "zoom out"
        const xPadding = (xMax - xMin) * 0.1;  // 10% padding on both sides
        const yPadding = (yMax - yMin) * 0.1;  // 10% padding on both sides

        return [
            ...scatterData,
            ...(hullTraces || []),
            {
              layout: {
                width: 600,
                height: 400,
                title: 'Wind Speed & Direction Clustering',
                xaxis: {
                  title: 'Wind Speed at 100m (m/s)',
                  range: [xMin - xPadding, xMax + xPadding],  // Set the x axis range with padding
                },
                yaxis: {
                  title: 'Wind Direction at 100m (deg)',
                  range: [yMin - yPadding, yMax + yPadding],  // Set the y axis range with padding
                },
                paper_bgcolor: 'transparent',
                plot_bgcolor: 'transparent',
                legend: { x: 1, y: 1 },
              },
            },
        ] as Partial<Plotly.Data>[];
    };
    
      return (
        <Box display="flex" flexDirection="column" alignItems="center">
            <Plot
                data={plotData()}
                layout={{
                    width: 600,
                    height: 400,
                    title: {text: 'Solution Space'},
                    xaxis: { showticklabels: false },
                    yaxis: { showticklabels: false },
                    paper_bgcolor: 'transparent',
                    plot_bgcolor: 'transparent',
                    legend: { x: 1, y: 1 },
                }}
            />
        </Box>
      );
    };

export default OffshoreClusterScatterPlot;