# pyMOODS in React

## Running Locally

### Starting the API Server

1. In the `dashboard` directory, create or activate a virtual environment. If you are using `venv`, run the following command:

```bash
source ./venv/Scripts/activate
```

2. Install the dependencies for your venv:

```bash
pip install -r requirements.txt
```

3. Run the following command to start the API server:

```bash
cd api
python react_api.py
```

The API should be running on `http://localhost:8080`

#### Starting the React App (Client)

1. In the `pymoods-react` directory, run the following to install the dependencies:

```bash
yarn install
```

2. Run the following to start the development server:

```bash
yarn dev
```

You can now access the React app on `http://localhost:80`.

## App Workflow

This app is designed to take the Plotly figures produced in python and render it in a React web app by utilizing a Flask API to get the plots.

To see a concrete example, follow the workflow of:
- `pymoods-react\src\components\OffshoreWindfarmPlots\ClusterScatterPlot.tsx` - the React component for the cluster scatter plot
- `dashboard\api\react_api.py` - the API
- `dashboard\dashlib\offshore_windfarm\screen3.py` - the source python script thet generated the plot

## Rendering a new Plot
If there is a new Plotly figure you have developed in Python and would like to render in React, follow these steps:
1. Ensure your python code returns a Plotly figure object (See cluster scatter plot for an example). Import or place that function in the API file - `dashboard\api\react_api.py`
2. Create an endpoint in the API file that returns the figure object as a JSON response. (See cluster scatter plot for an example)
3. Duplicate and modify the `NewPlotTemplate.tsx` file to create a new React component. Update the API endpoint used to the new endpoint URL you created in step 2.
4. Render your new component in the `MainGrid.tsx` or wherever else appropriate.