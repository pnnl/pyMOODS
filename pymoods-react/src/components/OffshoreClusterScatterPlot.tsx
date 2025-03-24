import { useState, useEffect } from 'react';
import Plotly from "plotly.js-basic-dist";
import createPlotlyComponent from "react-plotly.js/factory";
import Papa from 'papaparse';
import Box from '@mui/material/Box';

const Plot = createPlotlyComponent(Plotly);

const CSV_FILES = [
    '/data/COTTONWOOD_2018.csv'
];

interface CsvRow {
    Year: number;
    Month: number;
    Day: number;
    Hour: number;
    Minute: number;
    'wind speed at 100m (m/s)': number;
    'wind direction at 100m (deg)': number;
    'wind speed at 140m (m/s)': number;
}

const OffshoreClusterScatterPlot: React.FC = () => {
    const [data, setData] = useState<CsvRow[]>([]);
    
    useEffect(() => {
        const fetchData = async () => {
          const allData: CsvRow[] = [];
    
          for (const file of CSV_FILES) {
            const response = await fetch(file);
            const csvText = await response.text();
    
            Papa.parse(csvText, {
              header: true,
              dynamicTyping: true,
              skipEmptyLines: true,
              complete: (results) => {
                const parsedData = results.data as CsvRow[];
    
                // Ensure valid numerical data
                const filteredData = parsedData.filter(
                  (row) =>
                    !isNaN(row['wind speed at 100m (m/s)']) &&
                    !isNaN(row['wind direction at 100m (deg)'])
                );
    
                allData.push(...filteredData);
                setData([...allData]);
              },
            });
          }
        };
    
        fetchData();
    }, []);

      const plotData = (): Partial<Plotly.Data>[] => {
        if (data.length === 0) return [];
    
        return [
            {
              x: data.map((row) => row['wind speed at 100m (m/s)']),
              y: data.map((row) => row['wind direction at 100m (deg)']),
              mode: 'markers',
              type: 'scatter',
              marker: { size: 6, color: data.map((row) => row['wind speed at 140m (m/s)']) },
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