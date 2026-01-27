// App.js

import React, { useEffect, useState } from 'react';
import Papa from 'papaparse';
import TimeSeriesChart from './components/TimeSeriesChart';
import ParallelCoordinatesChart from './components/ParallelCoordinatesChart';
import ScatterPlotChart from './components/ScatterPlotChart'; // Import the new component

const App = () => {
  const [data, setData] = useState([]);
  const [activeTab, setActiveTab] = useState('time-series');

  useEffect(() => {
    Papa.parse('scenarios.csv', {
      download: true,
      header: true,
      skipEmptyLines: true,
      dynamicTyping: true,
      complete: (results) => {
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

        setData(parsedData);
      },
      error: (error) => {
        console.error('Error loading CSV:', error);
      }
    });
  }, []);

  return (
    <div style={{ padding: '20px' }}>
      <h1>Visualizer</h1>

      {/* Tabs */}
      <div style={{ marginBottom: '10px' }}>
        <button onClick={() => setActiveTab('time-series')}>Time Series</button>
        <button onClick={() => setActiveTab('parallel-coords')}>Parallel Coordinates</button>
        <button onClick={() => setActiveTab('scatter-plot')}>Scatter Plot</button>
      </div>

      {/* Tab Content */}
      {activeTab === 'time-series' && data.length > 0 && (
        <TimeSeriesChart data={data} />
      )}

      {activeTab === 'parallel-coords' && data.length > 0 && (
        <ParallelCoordinatesChart data={data} />
      )}

      {activeTab === 'scatter-plot' && data.length > 0 && (
        <ScatterPlotChart data={data} />
      )}

      {data.length === 0 && <p>Loading data...</p>}
    </div>
  );
};

export default App;