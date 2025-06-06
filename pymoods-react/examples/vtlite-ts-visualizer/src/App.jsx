// src/App.jsx
import React, { useEffect, useState } from 'react';
import Papa from 'papaparse';
import TimeSeriesChart from './components/TimeSeriesChart';

const App = () => {
  const [data, setData] = useState([]);

  useEffect(() => {
    Papa.parse('scenarios.csv', {
      download: true,
      header: true,
      skipEmptyLines: true,
      dynamicTyping: true,
      complete: (results) => {
        console.log("First row of CSV:", results.data[0]);
        const parsedData = results.data.map(row => ({
          config: row.config,
          sim: parseInt(row.sim),
          time: parseFloat(row.time),
          ChS: parseFloat(row.ChS),
          DisS: parseFloat(row.DisS),
          SCS: parseFloat(row.SCS),
          WPQ: parseFloat(row.WPQ),
          WSQ: parseFloat(row.WSQ),
          kBS: parseFloat(row.kBS),
          kWS: parseFloat(row.kWS),
          lam_DAQ: parseFloat(row.lam_DAQ),
          lam_RT: parseFloat(row.lam_RT),
          pRBDS: parseFloat(row.pRBDS),
          pRBUS: parseFloat(row.pRBUS),
          pRWDS: parseFloat(row.pRWDS),
          pRWUS: parseFloat(row.pRWUS),
          pWDSQ: parseFloat(row.pWDSQ),
          pWRS: parseFloat(row.pWRS),
          pWSQ: parseFloat(row.pWSQ),
          v1: parseFloat(row.v1),
          v2: parseFloat(row.v2),
          WS: parseFloat(row.WS),
          pWDS: parseFloat(row.pWDS),
          pWS: parseFloat(row.pWS),
          CaseStudy: row["Case Study"],
          Location: row.Location,
        }));

        console.log('Parsed Data:', parsedData);
        setData(parsedData);
      },
      error: (error) => {
        console.error('Error loading CSV:', error);
      }
    });
  }, []);

  return (
    <div style={{ padding: '20px' }}>
      <h1>Time Series Visualizer</h1>
      {data.length > 0 ? (
        <TimeSeriesChart data={data} />
      ) : (
        <p>Loading data...</p>
      )}
    </div>
  );
};

export default App;
