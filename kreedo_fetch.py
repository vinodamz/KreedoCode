import requests
import csv
import time
import os
import json
from urllib.parse import urlparse

# --- HEADERS ---
# These headers will be sent with every request to the API.
# The Authorization token may need to be updated if it expires.
HEADERS = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.9',
    'Authorization': 'JWT eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxNjk3NzYsInVzZXJuYW1lIjoidHJ1c3RpbmdBcHBsZXM0IiwiZXhwIjoxNzc2MTU5MzQwLCJlbWFpbCI6ImluZm9AdGhlbGl0dGxlZ3JhZHVhdGVzLmluIiwib3JpZ19pYXQiOjE3NDQ2MjMzNDB9.12CCcPC82TcHPQe95NUUtsvif2gfMvRsLi0ODUoPhI4',
    'Origin': 'http://15.206.241.219',
    'Referer': 'http://15.206.241.219/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'cross-site',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Safari/605.1.15'
}

def fetch_and_save_responses(start_id, end_id, base_folder='kreedo_responses', csv_filename='kreedo_log.csv'):
    """
    Fetches activity data from the Kreedo API using auth headers, saves the
    full JSON response to a file, and logs the action to a CSV.

    Args:
        start_id (int): The first activity ID to check.
        end_id (int): The last activity ID to check.
        base_folder (str): The main folder to store all JSON responses.
        csv_filename (str): The name of the output log CSV file.
    """
    base_api_url = "https://6t.kreedo.solutions/api/activity/activity_detail_mob/{}"
    
    os.makedirs(base_folder, exist_ok=True)
    file_exists = os.path.isfile(csv_filename)
    
    with open(csv_filename, 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['activity_id', 'activity_name', 'status', 'json_file_path']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        print(f"Starting process for IDs {start_id} to {end_id}.")
        print(f"JSON responses will be saved in '{base_folder}' folder.")
        print(f"Using Authorization token for user: trustingApples4")

        for activity_id in range(start_id, end_id + 1):
            api_url = base_api_url.format(activity_id)
            json_save_path = ''
            
            try:
                # Use the global HEADERS for the API request
                response = requests.get(api_url, timeout=10, headers=HEADERS)
                if response.status_code != 200:
                    status_message = f"Failed with Status Code: {response.status_code}"
                    print(f"ID {activity_id}: {status_message}")
                    if response.status_code == 401:
                        print("    -> Unauthorized. The JWT token may be expired or invalid.")
                    writer.writerow({
                        'activity_id': activity_id,
                        'activity_name': 'N/A',
                        'status': status_message,
                        'json_file_path': ''
                    })
                    continue

                json_data = response.json()
                if not json_data.get('isSuccess'):
                    status_message = "API reported failure"
                    print(f"ID {activity_id}: {status_message}")
                    writer.writerow({
                        'activity_id': activity_id,
                        'activity_name': 'N/A',
                        'status': status_message,
                        'json_file_path': ''
                    })
                    continue

                data = json_data.get('data', {})
                activity_name = data.get('name', 'N/A')
                print(f"\nProcessing ID {activity_id}: Fetched '{activity_name}'")

                # Create a dedicated folder for this activity's response
                activity_folder = os.path.join(base_folder, str(activity_id))
                os.makedirs(activity_folder, exist_ok=True)
                
                # Save the full JSON response
                json_save_path = os.path.join(activity_folder, f"{activity_id}_response.json")
                with open(json_save_path, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=4)
                
                print(f"    -> Successfully saved JSON response to {json_save_path}")

                # Log success to CSV
                writer.writerow({
                    'activity_id': activity_id,
                    'activity_name': activity_name,
                    'status': 'Success',
                    'json_file_path': json_save_path
                })

            except requests.exceptions.RequestException as e:
                print(f"ID {activity_id}: Network error: {e}")
                writer.writerow({'activity_id': activity_id, 'activity_name': 'N/A', 'status': f'Network Error: {e}', 'json_file_path': ''})
            except ValueError:
                print(f"ID {activity_id}: Failed to decode JSON.")
                writer.writerow({'activity_id': activity_id, 'activity_name': 'N/A', 'status': 'JSON Decode Error', 'json_file_path': ''})
            
            time.sleep(0.5)

    print(f"\nProcess complete. Log file is in '{csv_filename}'.")


# --- How to use it ---
if __name__ == "__main__":
    # Define the range of IDs you want to fetch.
    START_ACTIVITY_ID = 10000
    END_ACTIVITY_ID = 10005
    
    fetch_and_save_responses(START_ACTIVITY_ID, END_ACTIVITY_ID)
