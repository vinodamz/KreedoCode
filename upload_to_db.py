import pandas as pd
import json
from pathlib import Path
from sqlalchemy import create_engine, exc

# --- DATABASE CONFIGURATION ---
# These details have been updated based on your screenshot.
# !! IMPORTANT: Replace 'your_actual_password' with your real password. !!
DB_CONFIG = {
    'user': 'lgdb',
    'password': 'Godaudha1#',
    'host': '190.92.174.130',
    'port': 3306,
    'database': 'lgschool'
}

def create_relational_dataframes(json_data):
    """
    Converts a single JSON object for a learning activity into a relational
    set of pandas DataFrames.
    """
    data = json_data.get('data', {})
    if not data or not data.get('id'):
        return None

    activity_id = data['id']
    
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

    all_dfs = {
        "activities": [], "materials": [], "assets": [],
        "activity_material_link": [], "activity_asset_link": []
    }

    json_files = list(root_dir.rglob("*_response.json"))
    if not json_files:
        print(f"No '*_response.json' files found in '{root_path}'.")
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
        print("No valid activity data was found.")
        return None

    final_dataframes = {}
    for key, df_list in all_dfs.items():
        if df_list:
            final_dataframes[key] = pd.concat(df_list, ignore_index=True)
        else:
            final_dataframes[key] = pd.DataFrame()

    if not final_dataframes["materials"].empty:
        final_dataframes["materials"] = final_dataframes["materials"].drop_duplicates(subset=['material_id']).reset_index(drop=True)
    
    if not final_dataframes["assets"].empty:
        final_dataframes["assets"] = final_dataframes["assets"].drop_duplicates(subset=['asset_id']).reset_index(drop=True)

    return final_dataframes

def write_to_mysql(dataframes_dict):
    """
    Writes a dictionary of DataFrames to a MySQL database using the configured credentials.
    """
    if not dataframes_dict:
        print("No dataframes to write to the database.")
        return

    # Check for placeholder password

    db_user = DB_CONFIG['user']
    db_password = DB_CONFIG['password']
    db_host = DB_CONFIG['host']
    db_port = DB_CONFIG['port']
    db_name = DB_CONFIG['database']

    conn_str = f"mysql+mysqlconnector://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    try:
        engine = create_engine(conn_str)
        print(f"\nConnecting to database '{db_name}' on {db_host}...")
        
        with engine.connect() as connection:
            print("Database connection successful.")
            
            for table_name, df in dataframes_dict.items():
                if df.empty:
                    print(f"Skipping empty table '{table_name}'.")
                    continue
                
                print(f"Writing data to table '{table_name}'...")
                df.to_sql(name=table_name, con=engine, if_exists='replace', index=False, chunksize=1000)
                print(f"Successfully wrote {len(df)} rows to '{table_name}'.")
        
        print("\nAll data has been successfully written to the database.")

    except exc.SQLAlchemyError as e:
        print(f"\nAn error occurred with the database operation.")
        print(f"Error details: {e}")
        print("Please check your database credentials, password, and ensure the server is running and accessible.")

# --- Main Execution ---
if __name__ == "__main__":
    curriculum_path = 'kreedo_responses'
    final_data = process_directory(curriculum_path)
    
    if final_data:
        write_to_mysql(final_data)