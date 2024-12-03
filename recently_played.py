import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
from prefect.blocks.system import Secret
from prefect import task, flow
import json
from google.oauth2 import service_account
import gspread
from datetime import datetime

# Google Sheets setup
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
SHEET_KEY = "1bWx69qOeSw4SinLdjxfFK-Ib6l2BzOAIjBGbeculCrc"  # Your Google Sheet key
WORKSHEET_NAME = "Recently Played"  # Name of the worksheet in the Google Sheet
service_account_secret_block = Secret.load("google-service-account")

# Spotify API setup
secret_block1 = Secret.load('spotify-client-secret')
secret_block2 = Secret.load('my-spotify-client-id')
SPOTIFY_CLIENT_ID = secret_block2.get()
SPOTIFY_CLIENT_SECRET = secret_block1.get()
SPOTIFY_REDIRECT_URI = 'http://localhost:8080/callback'
SPOTIFY_SCOPE = 'user-read-recently-played'

# Configure pandas display settings
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)

# Authorize Google Sheets API
# Load the Prefect Secret block
service_account_secret_block = Secret.load("google-service-account")

# Get the credentials directly (no need for json.loads())
service_account_info = service_account_secret_block.get()
credentials = service_account.Credentials.from_service_account_info(service_account_info, scopes=SCOPE)

@task
def get_google_sheet():
    client = gspread.authorize(credentials)
    # Open Google Sheet by its key and get the worksheet
    sheet = client.open_by_key(SHEET_KEY)
    worksheet = sheet.worksheet(WORKSHEET_NAME)
    return worksheet


@task
def get_recently_played():
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope=SPOTIFY_SCOPE
    ))
    results = sp.current_user_recently_played(limit=50)
    return [
        {
            'played_at': track['played_at'],
            'track_name': track['track']['name'],
            'artist_name': ', '.join(artist['name'] for artist in track['track']['artists']),
            'album_name': track['track']['album']['name'],
            'duration_seconds': track['track']['duration_ms'] / 1000  # Convert milliseconds to seconds
        }
        for track in results['items']
    ]

@task
def create_dataframe(data):
    # Create a DataFrame from the list of track data
    df = pd.DataFrame(data)
    df['played_at'] = pd.to_datetime(df['played_at'])
    return df

@task
def get_existing_timestamps(worksheet):
    # Get all values in the 'played_at' column (assuming it's the first column)
    existing_data = worksheet.col_values(1)[1:]  # Skip the header
    return set(existing_data)  # Convert to a set for quick lookup

@task
def update_google_sheet(worksheet, df, existing_timestamps):
    # Filter out rows that already exist in the Google Sheet
    new_data = [
        [
            row['played_at'].strftime('%Y-%m-%d %H:%M:%S'),  # Format datetime to string
            row['track_name'],
            row['artist_name'],
            row['album_name'],
            row['duration_seconds']
        ]
        for _, row in df.iterrows()
        if row['played_at'].strftime('%Y-%m-%d %H:%M:%S') not in existing_timestamps
    ]

    if new_data:
        # Insert the new rows starting at row 2
        worksheet.insert_rows(new_data, row=2)
        print(f"Inserted {len(new_data)} new rows.")
    else:
        print("No new rows to insert.")

@flow
def update_recently_played():
    # Fetch Spotify data
    played_tracks = get_recently_played()

    # Create DataFrame
    df = create_dataframe(played_tracks)

    # Get Google Sheet
    worksheet = get_google_sheet()

    # Get existing timestamps from Google Sheet
    existing_timestamps = get_existing_timestamps(worksheet)

    # Update Google Sheet
    update_google_sheet(worksheet, df, existing_timestamps)

    print(f"Updated Google Sheet with {len(df)} tracks.")

if __name__ == "__main__":
    update_recently_played()


#print_dataframe_deployment = print_dataframe.to_deployment(
 #   name='Create Recently Played Datafarame', cron="00 21 * * *")

