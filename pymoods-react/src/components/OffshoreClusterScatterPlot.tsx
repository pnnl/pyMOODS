import { useState, useEffect } from 'react';
import Plotly from "plotly.js-basic-dist";
import createPlotlyComponent from "react-plotly.js/factory";
import Papa from 'papaparse';
import Box from '@mui/material/Box';

const Plot = createPlotlyComponent(Plotly);

interface CsvRow {
    
}

const OffshoreClusterScatterPlot: React.FC = () => {
    const [data, setData] = useState<any[]>([]);
    const [columns, setColumns] = useState<string[]>([]);

    useEffect(() => {
        // Load and parse the CSV file
        const fetchData = async () => {
          const response = await fetch('/data/*.csv');
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
    
        return [
          {
            // type: 'scatter',
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
                    paper_bgcolor: 'transparent',
                    plot_bgcolor: 'transparent',
                }}
            />
        </Box>
      );
    };

export default OffshoreClusterScatterPlot;