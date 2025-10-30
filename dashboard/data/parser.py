import base64
import json
import pandas as pd

def parse_data(content, filename=None):
    if filename:
        content_type, content_string = content.split(",")
        decoded = base64.b64decode(content_string)
        file = json.loads(decoded)
        df =  pd.DataFrame(file)
    else:
        df = pd.read_json(content, orient='records')

    # Categorize variables into 'Decision Variables' and 'Objective Functions'
    
    decision_variables = {key: df[key].tolist() for key in df.columns if key.startswith('x')}
    objective_functions = {key: df[key].tolist() for key in df.columns if key.startswith('f')}

    return df, decision_variables, objective_functions