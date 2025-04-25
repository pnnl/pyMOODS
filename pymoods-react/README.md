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

You can now access the React app on `http://localhost:443`.