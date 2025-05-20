import h5py
import numpy as np
import pandas as pd 

# Open the file (read-only mode)
def read_as_df(file_obj, key, s21):
    # output dictionary
    out_dict = {}
    
    # references
    refs = file_obj[file_obj[key][()][0]][:]
    counter = 0
    for r in refs:
        scenario_num = file_obj[file_obj[r][()][0]][()]
        if scenario_num in list(s21.keys()):
            for act_scenario in s21[scenario_num]:
                out_dict[f"{key} {act_scenario}"] = np.squeeze(file_obj[file_obj[r][()][1]][:])
        else:
            out_dict[f"{key} {scenario_num}"] = np.squeeze(file_obj[file_obj[r][()][1]][:])
        counter += 1

    # return dataframe
    return pd.DataFrame(out_dict)

# Open the file (read-only mode)
def read_s21_as_df(file_obj, key):
    # output dictionary
    out_dict = {}
    
    # references
    refs = file_obj[file_obj[key][()][0]][:]
    counter = 0
    for r in refs:
        scenario_num = int(file_obj[file_obj[r][()][0]][()])
        out_dict[scenario_num] = np.squeeze(file_obj[file_obj[r][()][1]][:])
        counter += 1

    # return dataframe
    return out_dict

# scaler_dict
def read_scaler_dict(filepath):
    with h5py.File(filepath, "r") as f:
        scaler_dict = {}
        # for each key
        for k in f.keys():
            # unable to read keys
            if k in ["PowerBase", "S1", "S2", "S21", "Wrate", "_types", "CSS", "SZS"]:
                if k in ["PowerBase", "Wrate", "S1", "S2", "CSS", "SZS"]:
                    scaler_dict[k] = f[k][()]
                elif k in ["S21"]:
                    scaler_dict[k] = read_s21_as_df(f, k)#.to_dict(orient='records')

    return scaler_dict

def read_timeseries(filepath, scaler_dict):
    with h5py.File(filepath, "r") as f:
        # Print all keys (groups/datasets)
        # print("Keys: ", list(f.keys()))
        
        # output lists
        list_of_df96s = []
        list_of_df24s = []
        
        df96_keys = []
        df24_keys = []
        
        # for each key
        for k in f.keys():
            if k in ["PowerBase", "S1", "S2", "S21", "Wrate", "_types", "CSS", "SZS"]:
                continue
            # unable to read keys
            elif k in ["pWDS", "pWS", "WS"]:
                df24_keys.append(k)
                list_of_df24s.append(read_as_df(f, k, scaler_dict["S21"]))
            # read as dataframe
            else:
                df96_keys.append(k)
                list_of_df96s.append(read_as_df(f, k, scaler_dict["S21"]))

    scaler_dict["keys96"] = df96_keys
    scaler_dict["keys24"] = df24_keys
    return pd.concat(list_of_df96s, axis=1), pd.concat(list_of_df24s, axis=1), scaler_dict
    
def realign_index(temp_df):
    # Split column names at spaces and create a MultiIndex
    # Here, we assume that each column name has distinct parts when split
    split_columns = [(col.split()[0], int(col.split()[1])) for col in temp_df.columns]
    multi_index = pd.MultiIndex.from_tuples(split_columns)
    
    # Assign the MultiIndex to the DataFrame columns
    temp_df.columns = multi_index

    temp_df_stacked = temp_df.stack(level=1, future_stack=True).swaplevel(0, 1)
    temp_df_stacked.index.names = ['sim', 'time']
    temp_df_stacked = temp_df_stacked.sort_index()

    return temp_df_stacked

def read_jld2_solution_file_as_df(filepath):
    scaler_dict = read_scaler_dict(filepath)
    df96, df24, scaler_dict = read_timeseries(filepath, scaler_dict)

    df96_realigned = realign_index(df96)
    
    # Number of times each row should be repeated
    repeat_count = 4
    
    # Use np.repeat to repeat the indices of the DataFrame
    repeated_indices = np.repeat(df24.index, repeat_count)
    
    # Use loc to select rows based on the repeated indices
    df24_repeated = df24.loc[repeated_indices].reset_index(drop=True)
    df24_realigned = realign_index(df24_repeated)

    # out frame
    df_out = pd.merge(df96_realigned, df24_realigned, left_index=True, right_index=True)

    # return 
    return df_out, scaler_dict

def read_kerntree(filepath):
    kerntree = dict()
    with h5py.File(filepath, "r") as f:
        kerntree["probability"] = f[f["KernTree"]["probability"]][:][0]
        kerntree["state"] = f[f["KernTree"]["state"]][:].T
        all_children = f[f["KernTree"]["children"]][:]
        kerntree["children"] = dict()
        for i in range(len(all_children)):
            kerntree["children"][i] = f[all_children[i]][:]
        kerntree["parent"] = f[f["KernTree"]["parent"]][:]

    return kerntree

def interpolate_states(w24_states):
    # Initialize States by interpolating between first and second column (5 points)
    states = np.linspace(w24_states[:, 0], w24_states[:, 1], 5).T
    
    for i in range(1, 23):  # 2 to 24-1 in Julia is 1 to 22 in Python (0-based)
        segment = np.linspace(w24_states[:, i], w24_states[:, i + 1], 5).T[:, 1:5]
        states = np.hstack((states, segment))  # Use middle 3 (index 1 to 3)

    # Append final 3 interpolated steps past last state
    for i in range(1, 4):
        new_state = w24_states[:, 23] + i * (w24_states[:, 23] - w24_states[:, 0]) / 4
        states = np.hstack((states, new_state[:, np.newaxis]))

    return states