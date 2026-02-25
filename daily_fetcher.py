import requests
import csv
import time
import os
import json
import random

jwt_token = "JWT eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxNjk3NzYsInVzZXJuYW1lIjoidHJ1c3RpbmdBcHBsZXM0IiwiZXhwIjoxNzc2MTU5MzQwLCJlbWFpbCI6ImluZm9AdGhlbGl0dGxlZ3JhZHVhdGVzLmluIiwib3JpZ19pYXQiOjE3NDQ2MjMzNDB9.12CCcPC82TcHPQe95NUUtsvif2gfMvRsLi0ODUoPhI4"
        
headers = {
            'Accept': 'application/json, text/plain, */*',
            'Authorization': jwt_token,
            'Origin': 'http://15.206.241.219',
            'Referer': 'http://15.206.241.219/',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Safari/605.1.15'
        }

def load_schedule(filename="schedule.json"):
    """Loads the activity schedule from a JSON file."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: The schedule file '{filename}' was not found.")
        print("Please run the 'create_schedule.py' script first to generate it.")
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{filename}'. The file might be corrupted.")
        return None

def fetch_and_save_responses(activity_ids, headers, base_folder='kreedo_responses', csv_filename='kreedo_log.csv'):
    """
    Fetches activity data from the Kreedo API for a list of IDs,
    skipping any that have already been downloaded.

    Args:
        activity_ids (list): A list of activity IDs to check for the current run.
        headers (dict): The request headers, including the auth token.
        base_folder (str): The main folder to store all JSON responses.
        csv_filename (str): The name of the output log CSV file.
    """
    os.makedirs(base_folder, exist_ok=True)
    file_exists = os.path.isfile(csv_filename)
    
    with open(csv_filename, 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['activity_id', 'activity_name', 'status', 'json_file_path']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        print(f"Starting process for {len(activity_ids)} IDs for this session.")
        
        for index, activity_id in enumerate(activity_ids):
            print(f"\n--- Progress: {index + 1} of {len(activity_ids)} ---")
            
            # Construct the expected path for the JSON file
            activity_folder = os.path.join(base_folder, str(activity_id))
            json_save_path = os.path.join(activity_folder, f"{activity_id}_response.json")

            # --- CHECK IF ALREADY DOWNLOADED ---
            if os.path.exists(json_save_path):
                print(f"ID {activity_id}: Already exists. Skipping.")
                # Optionally, you could log this skip, but for now we just move on.
                continue

            api_url = f"https://6t.kreedo.solutions/api/activity/activity_detail_mob/{activity_id}"
            
            try:
                response = requests.get(api_url, timeout=15, headers=headers)
                
                if response.status_code != 200:
                    status_message = f"Failed with Status Code: {response.status_code}"
                    print(f"ID {activity_id}: {status_message}")
                    if response.status_code == 401:
                        print("    -> UNAUTHORIZED. The JWT token is likely expired or invalid.")
                    writer.writerow({'activity_id': activity_id, 'activity_name': 'N/A', 'status': status_message, 'json_file_path': ''})
                    continue

                json_data = response.json()
                
                if not json_data.get('isSuccess'):
                    status_message = "API reported failure"
                    print(f"ID {activity_id}: {status_message}")
                    writer.writerow({'activity_id': activity_id, 'activity_name': 'N/A', 'status': status_message, 'json_file_path': ''})
                    continue

                data = json_data.get('data', {})
                activity_name = data.get('name', 'N/A')
                print(f"Processing ID {activity_id}: Fetched '{activity_name}'")

                os.makedirs(activity_folder, exist_ok=True)
                
                with open(json_save_path, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=4)
                
                print(f"    -> Saved JSON response to {json_save_path}")
                writer.writerow({
                    'activity_id': activity_id, 'activity_name': activity_name,
                    'status': 'Success', 'json_file_path': json_save_path
                })

            except requests.exceptions.RequestException as e:
                print(f"ID {activity_id}: Network error: {e}")
                writer.writerow({'activity_id': activity_id, 'activity_name': 'N/A', 'status': f'Network Error: {e}', 'json_file_path': ''})
            
            # --- RANDOM DELAY ---
            # sleep_time = random.uniform(0.5, 1)
            # print(f"    -> Sleeping for {sleep_time:.2f} seconds...")
            # time.sleep(sleep_time)

    print(f"\nProcess complete for this session.")

# --- How to use it ---
if __name__ == "__main__":
    schedule = load_schedule()
    
    print("Starting to process all days in the schedule...")

for day_key, daily_ids in schedule.items():
    # Extract the day number from the key (e.g., 'day_1' -> '1')
    day_number = day_key.split('_')[-1]
    
    print("-" * 40)
    
    if daily_ids:
        print(f"Day {day_number}: Will process {len(daily_ids)} IDs.")
        # Call the function to process the IDs for the current day
        fetch_and_save_responses(daily_ids, headers)
    else:
        print(f"Day {day_number}: No IDs to process.")

print("-" * 40)
print("Processing complete for all days.")
