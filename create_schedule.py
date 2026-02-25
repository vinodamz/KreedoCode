import json
import random
import math
import os

class ActivityScheduler:
    """
    Creates a randomized daily schedule for fetching activities and saves it to a JSON file.
    """
    def __init__(self, start_id, end_id, num_days):
        """
        Initializes the scheduler with the activity range and duration.

        Args:
            start_id (int): The first activity ID in the range.
            end_id (int): The last activity ID in the range.
            num_days (int): The number of days to split the activities across.
        """
        if not (isinstance(start_id, int) and isinstance(end_id, int) and isinstance(num_days, int)):
            raise ValueError("All arguments must be integers.")
        if start_id >= end_id:
            raise ValueError("start_id must be less than end_id.")
        if num_days <= 0:
            raise ValueError("num_days must be a positive number.")
            
        self.start_id = start_id
        self.end_id = end_id
        self.num_days = num_days
        self.schedule = {}

    def create_schedule(self):
        """
        Generates the randomized schedule.
        
        It creates a master list of all IDs, shuffles it once, and then
        splits it into equal-sized chunks for each day.
        """
        print("Generating a randomized 30-day schedule...")
        
        # 1. Create a master list of all IDs
        master_id_list = list(range(self.start_id, self.end_id + 1))
        
        # 2. Shuffle the master list once to ensure IDs are random across all days
        random.shuffle(master_id_list)
        
        # 3. Split the shuffled list into chunks for each day
        total_ids_count = len(master_id_list)
        ids_per_day = math.ceil(total_ids_count / self.num_days)
        
        day_chunks = [
            master_id_list[i:i + ids_per_day]
            for i in range(0, total_ids_count, ids_per_day)
        ]
        
        # 4. Store the schedule in a dictionary with keys like "day_1", "day_2", etc.
        self.schedule = {f"day_{i+1}": chunk for i, chunk in enumerate(day_chunks)}
        
        print("Schedule created successfully.")
        return self.schedule

    def save_schedule_to_json(self, filename="schedule.json"):
        """
        Saves the generated schedule to a JSON file.

        Args:
            filename (str): The name of the file to save the schedule to.
        """
        if not self.schedule:
            print("No schedule to save. Please run create_schedule() first.")
            return

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.schedule, f, indent=4)
            
            # Get the full path for clarity
            full_path = os.path.abspath(filename)
            print(f"Schedule saved successfully to: {full_path}")

        except IOError as e:
            print(f"Error saving file: {e}")

# --- How to use it ---
if __name__ == "__main__":
    # Define the total range and duration
    TOTAL_START_ID = 920
    TOTAL_END_ID = 19800
    NUM_DAYS = 5
    
    # 1. Create an instance of the scheduler
    scheduler = ActivityScheduler(
        start_id=TOTAL_START_ID,
        end_id=TOTAL_END_ID,
        num_days=NUM_DAYS
    )
    
    # 2. Generate the schedule
    scheduler.create_schedule()
    
    # 3. Save the schedule to a file
    scheduler.save_schedule_to_json("schedule.json")
    
    # Optional: Print the number of activities for the first day as a check
    if scheduler.schedule:
        print(f"\nVerification: Day 1 has {len(scheduler.schedule.get('day_1', []))} activities scheduled.")

