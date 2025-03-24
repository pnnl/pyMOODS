import { useState, useEffect } from 'react';
import Plotly from "plotly.js-basic-dist";
import createPlotlyComponent from "react-plotly.js/factory";
import Papa from 'papaparse';
import Box from '@mui/material/Box';

const Plot = createPlotlyComponent(Plotly);

interface CsvRow {
    INTERVALSTARTTIME_GMT: string;
    LMP: string;
    [key: string]: any;
}

const LMPPlot: React.FC = () => {
    const [data, setData] = useState<any[]>([]);
    const [columns, setColumns] = useState<string[]>([]);

    useEffect(() => {
        // Load and parse the CSV file
        const fetchData = async () => {
          const response = await fetch('/data/LMP.csv');
          const reader = response.body?.getReader();
          const result = await reader?.read();
          const decoder = new TextDecoder('utf-8');
          const csv = decoder.decode(result?.value);
          Papa.parse(csv, {
            header: true,
            dynamicTyping: true,
            complete: (results) => {
              setColumns(Object.keys(results.data[0] as CsvRow));
              setData(results.data);
            },
          });
        };
    
        fetchData();
      }, []);

      const plotData = (): Partial<Plotly.Data>[] => {
        if (data.length === 0) return [];
    
        const parsedData = data.map(row => ({
          ...row,
          INTERVALSTARTTIME_GMT: new Date(row.INTERVALSTARTTIME_GMT)
        }));
    
        const hourlyLMP = parsedData.reduce((acc, row) => {
          const hour = row.INTERVALSTARTTIME_GMT.getHours();
          if (!acc[hour]) acc[hour] = [];
          acc[hour].push(row.LMP);
          return acc;
        }, {});
    
        const hourlyLMPMean = Object.keys(hourlyLMP).map(hour => {
          const lmpValues = hourlyLMP[hour];
          const validLMPValues = lmpValues.filter((val: number) => !isNaN(val));
          const meanLMP = validLMPValues.reduce((sum: any, val: any) => sum + val, 0) / validLMPValues.length;
  
          return {
              hour: parseInt(hour),
              LMP: meanLMP
          };
        });
    
        const x = hourlyLMPMean.map(row => row.hour);
        const y = hourlyLMPMean.map(row => row.LMP);
    
        return [
          {
            x,
            y,
            type: 'scatter',
            mode: 'lines',
            marker: { color: 'blue' },
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
                    title: {text: 'LMP'},
                    xaxis: { title: { text: 'Hour', standoff: 10 }, showgrid: true, showline: true, zeroline: true, linecolor: 'black', tickcolor: 'black', ticks: 'outside', ticklen: 5 },
                    yaxis: { title: { text: 'LMP', standoff: 10 }, showgrid: true, showline: true, zeroline: true, linecolor: 'black', tickcolor: 'black', ticks: 'outside', ticklen: 5 },
                    paper_bgcolor: 'transparent',
                    plot_bgcolor: 'transparent',
                }}
            />
        </Box>
      );
    };

export default LMPPlot;