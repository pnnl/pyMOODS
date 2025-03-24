import { useState, useEffect } from 'react';
import Plotly from "plotly.js-basic-dist";
import createPlotlyComponent from "react-plotly.js/factory";
import Papa from 'papaparse';
import Box from '@mui/material/Box';

const Plot = createPlotlyComponent(Plotly);

const CSV_FILE = '/data/COTTONWOOD_2018.csv';

interface CsvRow {
    Year: number;
    Month: number;
    Day: number;
    Hour: number;
    Minute: number;
    windSpeed100m: number;
    windDirection100m: number;
    windSpeed140m: number;
}

const OffshoreClusterScatterPlot: React.FC = () => {
    const [data, setData] = useState<CsvRow[]>([]);
    
    useEffect(() => {
        const fetchData = async () => {
          const response = await fetch(CSV_FILE);
          const csvText = await response.text();
    
          Papa.parse(csvText, {
            skipEmptyLines: true,
            dynamicTyping: true,
            complete: (results) => {
              const rawRows = results.data as string[][];
    
              // Find the actual data start row (where "Year" is the first column)
              const headerRowIndex = rawRows.findIndex((row) => row[0] === 'Year');
              if (headerRowIndex === -1) return;
    
              const headers = rawRows[headerRowIndex] as string[];
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
              }));
    
              setData(parsedData);
            },
          });
        };
    
        fetchData();
    }, []);

      const plotData = (): Partial<Plotly.Data>[] => {
        if (data.length === 0) return [];
    
        return [
            {
              x: data.map((row) => row.windSpeed100m),
              y: data.map((row) => row.windDirection100m),
              mode: 'markers',
              type: 'scatter',
              marker: { 
                size: 6, 
                color: data.map((row) => row.windSpeed140m),
                colorscale: 'Viridis', 
                showscale: true,
              },
              name: 'Wind Clusters',
            },
        ];
      };
    
      return (
        <Box display="flex" flexDirection="column" alignItems="center">
            <Plot
                data={plotData()}
                layout={{
                    width: 450,
                    height: 325,
                    title: {text: 'Solution Space'},
                    xaxis: { title: 'Wind Speed at 100m (m/s)' },
                    yaxis: { title: 'Wind Direction at 100m (deg)' },
                    paper_bgcolor: 'transparent',
                    plot_bgcolor: 'transparent',
                }}
            />
        </Box>
      );
    };

export default OffshoreClusterScatterPlot;