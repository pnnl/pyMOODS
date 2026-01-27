# import json
# import pandas as pd

# def csv_to_json(csv_file):
#     df = pd.read_csv(csv_file)
#     return df.to_dict(orient = 'records')

# def prepare_graph_data(json_data,mocodo24):
#     with open(mocodo24, 'r') as file:
#         config = json.load(file)
        
#     decision_variables = config.get("decision_variables", {})
#     objective_functions = config.get("objective_functions", {})
    
#     decision_cols = [key for key in decision_variables.keys()]
#     objective_cols = [key for key in objective_functions.keys()]
    
#     return decision_cols, objective_cols