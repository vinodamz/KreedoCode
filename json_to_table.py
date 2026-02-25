import pandas as pd
import json
from pathlib import Path

def create_relational_dataframes(json_data):
    """
    Converts a single JSON object for a learning activity into a relational
    set of pandas DataFrames. Skips the file if essential data is missing.
    """
    data = json_data.get('data', {})
    # Ensure the record has an ID to be useful
    if not data or not data.get('id'):
        return None

    activity_id = data['id']

    # --- Extract core objects and their links ---
    activities_df = pd.DataFrame([{
        'activity_id': activity_id,
        'name': data.get('name'),
        'type': data.get('type'),
        'objective': data.get('objective'),
        'description': data.get('description')
    }])

    master_material_list = data.get('master_material', [])
    materials_df = pd.DataFrame(master_material_list).rename(columns={'id': 'material_id'})
    
    activity_asset_list = data.get('activity_asset', [])
    assets_df = pd.DataFrame(activity_asset_list).rename(columns={'id': 'asset_id'})

    activity_material_link_df = pd.DataFrame()
    if not materials_df.empty:
        activity_material_link_df = pd.DataFrame({
            'activity_id': activity_id,
            'material_id': materials_df['material_id']
        })

    activity_asset_link_df = pd.DataFrame()
    if not assets_df.empty:
       activity_asset_link_df = pd.DataFrame({
           'activity_id': activity_id,
           'asset_id': assets_df['asset_id']
       })

    return {
        "activities": activities_df,
        "materials": materials_df,
        "assets": assets_df,
        "activity_material_link": activity_material_link_df,
        "activity_asset_link": activity_asset_link_df
    }

def process_directory(root_path):
    """
    Iterates through a directory, processes all response JSON files,
    and returns a consolidated set of DataFrames.
    """
    root_dir = Path(root_path)
    if not root_dir.is_dir():
        print(f"Error: Directory not found at '{root_path}'")
        return None

    # Lists to hold data from all files
    all_dfs = {
        "activities": [], "materials": [], "assets": [],
        "activity_material_link": [], "activity_asset_link": []
    }

    # Find all JSON files recursively
    json_files = list(root_dir.rglob("*_response.json"))
    if not json_files:
        print(f"No '*_response.json' files found in '{root_path}'. Please check the folder and file names.")
        return None
        
    print(f"Found {len(json_files)} JSON file(s) to process...")

    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            result = create_relational_dataframes(data)
            
            if result:
                for key in all_dfs.keys():
                    if not result[key].empty:
                        all_dfs[key].append(result[key])
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Warning: Could not process file {file_path}. Error: {e}")

    if not all_dfs["activities"]:
        print("No valid activity data was found to create final DataFrames.")
        return None

    # --- Consolidate the lists into final DataFrames ---
    final_dataframes = {}
    for key, df_list in all_dfs.items():
        if df_list:
            final_dataframes[key] = pd.concat(df_list, ignore_index=True)
        else:
            # Create an empty DataFrame if no data was found for this key
            final_dataframes[key] = pd.DataFrame()

    # Drop duplicates to create the master lists
    if not final_dataframes["materials"].empty:
        final_dataframes["materials"] = final_dataframes["materials"].drop_duplicates(subset=['material_id']).reset_index(drop=True)
    
    if not final_dataframes["assets"].empty:
        final_dataframes["assets"] = final_dataframes["assets"].drop_duplicates(subset=['asset_id']).reset_index(drop=True)

    return final_dataframes


# --- Main Execution ---
# The script starts running from here.
if __name__ == "__main__":
    # Define the path to your main folder.
    # The script assumes 'kreedo_responses' is in the same directory.
    curriculum_path = 'kreedo_responses'
    
    # Process the directory and get the final, consolidated data.
    final_data = process_directory(curriculum_path)
    
    # Print the final, consolidated DataFrames
    if final_data:
        print("\n--- Processing Complete. Final DataFrames: ---")
        for name, df in final_data.items():
            print(f"\n--- {name.replace('_', ' ').title()} ---")
            if df.empty:
                print("No data found.")
            else:
                print(df.to_markdown(index=False))