import pandas as pd
import os
from typing import Optional, List, Tuple, Set
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from collections import Counter


class GoogleSheetsClient:
    """Handles Google Sheets API operations."""

    def __init__(self, service_account_file: str):
        self.service_account_file = service_account_file
        self.scopes = ['https://www.googleapis.com/auth/spreadsheets.readonly']
        self._service = None

    def _authenticate(self) -> bool:
        """Authenticate with Google Sheets API."""
        if not os.path.exists(self.service_account_file):
            print(f"ERROR: Service account key file not found at '{self.service_account_file}'")
            return False

        try:
            creds = Credentials.from_service_account_file(
                self.service_account_file,
                scopes=self.scopes
            )
            self._service = build('sheets', 'v4', credentials=creds)
            return True
        except Exception as e:
            print(f"Authentication failed: {e}")
            return False

    def read_sheet(self, spreadsheet_id: str, sheet_name: str) -> Optional[List[List[str]]]:
        """Read all data from a specific Google Sheet tab."""
        if not self._service and not self._authenticate():
            return None

        try:
            sheet = self._service.spreadsheets()
            result = sheet.values().get(
                spreadsheetId=spreadsheet_id,
                range=sheet_name
            ).execute()

            values = result.get('values', [])
            if not values:
                print(f'No data found in sheet: {sheet_name}')
                return None

            print(f"Successfully read {len(values)} rows from {sheet_name}")
            return values

        except HttpError as err:
            print(f"API error occurred: {err}")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None


class ActivityDataProcessor:
    """Processes and manages activity data from Google Sheets."""

    def __init__(self):
        self.activity_df: Optional[pd.DataFrame] = None
        self.activity_details_df: Optional[pd.DataFrame] = None
        self.merged_df: Optional[pd.DataFrame] = None

    def create_dataframe(self, sheet_data: List[List[str]]) -> Optional[pd.DataFrame]:
        """Create a pandas DataFrame from sheet data."""
        if not sheet_data or len(sheet_data) < 2:
            print("Insufficient data to create DataFrame")
            return None

        # Find the maximum number of columns
        max_cols = max(len(row) for row in sheet_data)

        # Pad all rows to max_cols with empty strings
        padded_data = [row + [''] * (max_cols - len(row)) for row in sheet_data]

        # Get headers and make them unique
        headers = padded_data[0]
        seen = Counter()
        unique_headers = []
        for h in headers:
            if seen[h] > 0:
                new_name = f"{h}_{seen[h]}" if h else f"Unnamed_{seen[h]}"
                unique_headers.append(new_name)
            else:
                unique_headers.append(h)
            seen[h] += 1

        data_rows = padded_data[1:]

        df = pd.DataFrame(data_rows, columns=unique_headers)
        if df.empty:
            print("Created DataFrame is empty")
            return None

        return df

    def clean_and_split_activities(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and split the 'Kreedo Activity Id/Title' column by multiple delimiters."""
        if 'Kreedo Activity Id/Title' not in df.columns:
            print("Warning: 'Kreedo Activity Id/Title' column not found")
            return df

        # Ensure column is string type
        df = df.copy()
        df['Kreedo Activity Id/Title'] = df['Kreedo Activity Id/Title'].astype(str)

        # Split by '$$' or ',' separators, allowing for whitespace around them.
        # This handles rows where activities are separated by commas instead of '$$'.
        df_split = df.assign(
            **{'Kreedo Activity Id/Title': df['Kreedo Activity Id/Title'].str.split(r'\s*(?:\$\$|,)\s*')}
        )

        # Explode to separate rows
        df_exploded = df_split.explode('Kreedo Activity Id/Title').reset_index(drop=True)

        # Clean up by stripping whitespace from each activity title and removing empty rows
        df_exploded['Kreedo Activity Id/Title'] = df_exploded['Kreedo Activity Id/Title'].str.strip()
        df_cleaned = df_exploded[df_exploded['Kreedo Activity Id/Title'] != ''].copy()

        return df_cleaned

    def merge_activity_details(self, child_df: pd.DataFrame, details_df: pd.DataFrame) -> pd.DataFrame:
        """Merge child activity log with activity details."""
        return pd.merge(
            child_df,
            details_df,
            left_on='LG Activity ID',
            right_on='Activity id',
            how='left'
        )

    def process_activity_data(self, sheet_data: List[List[str]]) -> bool:
        """Process main activity sheet data."""
        df = self.create_dataframe(sheet_data)
        if df is None:
            return False

        self.activity_df = self.clean_and_split_activities(df)
        print("Activity data processed successfully")
        return True

    def process_activity_details(self, sheet_data: List[List[str]]) -> bool:
        """Process activity details sheet data."""
        self.activity_details_df = self.create_dataframe(sheet_data)
        if self.activity_details_df is None:
            return False

        print("Activity details processed successfully")
        return True

    def merge_data(self) -> bool:
        """Merge activity data with details."""
        if self.activity_df is None or self.activity_details_df is None:
            print("Cannot merge: missing required data")
            return False

        self.merged_df = self.merge_activity_details(self.activity_df, self.activity_details_df)
        print("Data merged successfully")
        return True


class ChildActivityFinder:
    """Finds and manages activities for specific children."""

    def __init__(self, merged_df: pd.DataFrame, group_names: Optional[List[str]] = None):
        self.merged_df = merged_df
        if group_names is None:
            # Default group names to include in every child's activity list
            self.group_names = ['pg,nur,lkg,ukg', 'pg', 'nur', 'lkg', 'ukg']
        else:
            self.group_names = [name.strip().lower() for name in group_names]

    def find_child_activities(self, child_name: str) -> Tuple[Set[str], Set[str]]:
        """Find all activities assigned to a specific child, including group activities."""
        if self.merged_df is None or self.merged_df.empty:
            print("No data available to search")
            return set(), set()

        print(f"\nSearching activities for child: '{child_name}'")

        # Filter for the specific child (case-insensitive)
        child_mask = (
            self.merged_df['Child Name/Group Name']
            .str.strip()
            .str.lower() == child_name.strip().lower()
        )

        # Filter for group activities
        group_mask = (
            self.merged_df['Child Name/Group Name']
            .str.strip()
            .str.lower()
            .isin(self.group_names)
        )

        # Combine masks to include child-specific and group activities
        combined_mask = child_mask | group_mask
        child_df = self.merged_df[combined_mask]

        if child_df.empty:
            print(f"No data found for child: {child_name}")
            return set(), set()

        # Get Kreedo activities
        kreedo_activities = set(child_df['Kreedo Activity Id/Title'].dropna().tolist())

        # Create merged activity descriptions
        child_df = child_df.copy()
        child_df['Merged Activity'] = (
            "Name: " + child_df['Activity Name'].fillna('N/A') +
            " | Type: " + child_df['Activity Type'].fillna('N/A') +
            " | Description: " + child_df['Activity Description'].fillna('N/A')
        )
        other_activities = set(child_df['Merged Activity'].tolist())

        return kreedo_activities, other_activities

    def display_child_activities(self, child_name: str) -> None:
        """Display all activities for a specific child."""
        kreedo_activities, other_activities = self.find_child_activities(child_name)

        if kreedo_activities:
            print(f"\nKreedo Activities for {child_name}:")
            for activity in sorted(kreedo_activities):
                print(f"- {activity}")
        else:
            print(f"No Kreedo activities found for {child_name}")

        if other_activities:
            print(f"\nOther Activities for {child_name}:")
            for activity in sorted(other_activities):
                print(f"- {activity}")
        else:
            print(f"No other activities found for {child_name}")

        return kreedo_activities, other_activities


class ActivityManager:
    """Main class that orchestrates the entire activity management system."""

    def __init__(self, service_account_file: str, spreadsheet_id: str):
        self.sheets_client = GoogleSheetsClient(service_account_file)
        self.spreadsheet_id = spreadsheet_id
        self.processor = ActivityDataProcessor()
        self.activity_finder: Optional[ChildActivityFinder] = None

    def load_data(self, activity_sheet_name: str, details_sheet_name: str) -> bool:
        """Load and process data from Google Sheets."""
        # Load activity sheet
        activity_data = self.sheets_client.read_sheet(self.spreadsheet_id, activity_sheet_name)
        if not activity_data:
            print(f"Failed to load activity sheet: {activity_sheet_name}")
            return False

        # Load activity details sheet
        details_data = self.sheets_client.read_sheet(self.spreadsheet_id, details_sheet_name)
        if not details_data:
            print(f"Failed to load details sheet: {details_sheet_name}")
            return False

        # Process both datasets
        if not self.processor.process_activity_data(activity_data):
            return False

        if not self.processor.process_activity_details(details_data):
            return False

        # Merge the data
        if not self.processor.merge_data():
            return False

        # Define common group names to include in every child's search
        common_activity_groups = ['pg,nur,lkg,ukg', 'pg', 'nur', 'lkg', 'ukg']

        # Initialize activity finder with the merged data and group names
        self.activity_finder = ChildActivityFinder(self.processor.merged_df, group_names=common_activity_groups)
        return True

    def find_child_activities(self, child_name: str) -> Tuple[Set[str], Set[str]]:
        """Find activities for a specific child."""
        if not self.activity_finder:
            print("Data not loaded. Please call load_data() first.")
            return set(), set()

        return self.activity_finder.find_child_activities(child_name)

    def display_child_activities(self, child_name: str) -> None:
        """Display activities for a specific child."""
        if not self.activity_finder:
            print("Data not loaded. Please call load_data() first.")
            return

        self.activity_finder.display_child_activities(child_name)

    def get_summary(self) -> dict:
        """Get a summary of the loaded data."""
        if self.processor.merged_df is None:
            return {"status": "No data loaded"}

        df = self.processor.merged_df
        return {
            "total_records": len(df),
            "unique_children": df['Child Name/Group Name'].nunique() if 'Child Name/Group Name' in df.columns else 0,
            "unique_activities": df['Kreedo Activity Id/Title'].nunique() if 'Kreedo Activity Id/Title' in df.columns else 0,
            "columns": list(df.columns)
        }


def main():
    """Main function demonstrating usage of the ActivityManager."""
    # Configuration
    SERVICE_ACCOUNT_FILE = 'little-graduates-3663b17fa316.json'
    SPREADSHEET_ID = '1appyzadECA12C_SMWpRODyDR2ovtvqBUwzSNfkbbXQ0'
    ACTIVITY_SHEET_NAME = "Activity Sheet"
    ACTIVITY_DETAILS_SHEET_NAME = "Activity Details"

    # Initialize the activity manager
    manager = ActivityManager(SERVICE_ACCOUNT_FILE, SPREADSHEET_ID)

    # Load and process data
    if not manager.load_data(ACTIVITY_SHEET_NAME, ACTIVITY_DETAILS_SHEET_NAME):
        print("Failed to load data. Exiting.")
        return

    # Display summary
    summary = manager.get_summary()
    print(f"\nData Summary: {summary}")

    # Find activities for a specific child
    child_name = 'zaren'
    manager.display_child_activities(child_name)
    
    # Find activities for another child to test comma separation
    child_name_2 = 'rayan'
    manager.display_child_activities(child_name_2)


if __name__ == "__main__":
    main()
