# pyMOODS in React

## Running Locally

To view pyMOODS in React, run the following commands:

1. In the `dashboard` directory, create or activate a venv and install the dependencies:

```bash
pip install -r requirements.txt
```

2. Activate the virtual environment. If you are using `venv`, run the following command:

```bash
source venv/Scripts/activate
```

3. In the `dashboard/api/` directory, run the following command to start the API server:

```bash
python app.py
```

4. In the `pymoods-react` directory, run the following command to install the dependencies:

```bash
yarn install
```

5. After the dependencies are installed, run the following command to start the development server:

```bash
yarn dev
```

The API should be running on `http://localhost:8080` and the React app should be running on `http://localhost:80`. You can access the app in your web browser by navigating to `http://localhost:8080`.