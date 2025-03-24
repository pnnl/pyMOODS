import { useState, useEffect } from 'react';
import Plotly from "plotly.js-basic-dist";
import createPlotlyComponent from "react-plotly.js/factory";
import Papa from 'papaparse';
import Box from '@mui/material/Box';

const Plot = createPlotlyComponent(Plotly);

const CSV_FILES = [
    { path: '/data/COTTONWOOD_2018.csv', label: 'Cottonwood', color: 'blue' },
    { path: '/data/JOHNDAY_2018.csv', label: 'Johnday', color: 'red' },
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
                    }
                },
            });
          }
        };
    
        fetchData();
    }, []);

      const plotData = (): Partial<Plotly.Data>[] => {
        if (data.length === 0) return [];
    
        return CSV_FILES.map((file) => ({
            x: data.filter((row) => row.site === file.label).map((row) => row.windSpeed100m),
            y: data.filter((row) => row.site === file.label).map((row) => row.windDirection100m),
            mode: 'markers',
            type: 'scatter',
            marker: {
              size: 6,
              color: file.color,
            },
            name: file.label,
        }));
      };
    
      return (
        <Box display="flex" flexDirection="column" alignItems="center">
            <Plot
                data={plotData()}
                layout={{
                    width: 600,
                    height: 400,
                    title: {text: 'Solution Space'},
                    xaxis: { title: 'Wind Speed at 100m (m/s)' },
                    yaxis: { title: 'Wind Direction at 100m (deg)' },
                    paper_bgcolor: 'transparent',
                    plot_bgcolor: 'transparent',
                    legend: { x: 1, y: 1 },
                }}
            />
        </Box>
      );
    };

export default OffshoreClusterScatterPlot;