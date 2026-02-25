# KreedoCode

A collection of Python scripts for fetching, processing, and generating content from the Kreedo educational platform API.

## Scripts

| Script | Purpose |
|--------|---------|
| `kreedo_fetch.py` | Fetch activity JSON responses for a hardcoded ID range |
| `create_schedule.py` | Split an ID range into daily chunks, saved to `schedule.json` |
| `daily_fetcher.py` | Run the full schedule, skipping already-downloaded IDs |
| `json_to_table.py` | Convert cached JSON responses into relational DataFrames |
| `Book_question.py` | Streamlit app to generate questions from PDFs using GPT-4o-mini |
| `process_live_sheet.py` | Read activity data from Google Sheets and find activities per child |

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# For Book_question.py
pip install streamlit langchain langchain-openai pydantic

# For process_live_sheet.py
pip install google-api-python-client google-auth
```

## Usage

```bash
# 1. Create a fetch schedule
python create_schedule.py   # edit TOTAL_START_ID, TOTAL_END_ID, NUM_DAYS at the bottom

# 2a. Fetch a specific ID range
python kreedo_fetch.py      # edit START_ACTIVITY_ID / END_ACTIVITY_ID at the bottom

# 2b. Fetch using the schedule (skips already-downloaded IDs)
python daily_fetcher.py

# 3. Convert cached responses to DataFrames
python json_to_table.py

# 4. Generate questions from a PDF (Streamlit UI)
streamlit run Book_question.py

# 5. Process Google Sheets activity data
python process_live_sheet.py
```

## Notes

- JWT token is hardcoded in `kreedo_fetch.py` and `daily_fetcher.py` — update it when you get 401 responses.
- `kreedo_responses/` stores 18 000+ cached JSON files — do not delete.
- `Book_question.py` requires an OpenAI API key set in the script.
- `process_live_sheet.py` requires a Google service account JSON key file.
