import base64
import json
import pandas as pd

def parse_data(contents, filename):
    content_type, content_string = contents.split(",")
    decoded = base64.b64decode(content_string)
    try:
        json_data = json.loads(decoded)
        if isinstance(json_data, list):
            df = pd.DataFrame(json_data)

            # Categorize variables into 'Decision Variables' and 'Objective Functions'
            decision_variables = {key: df[key].tolist() for key in df.columns if key.startswith('x')}
            objective_functions = {key: df[key].tolist() for key in df.columns if key.startswith('f')}

            return df, decision_variables, objective_functions

    except Exception as e:
        print(e)
        return None, None, None