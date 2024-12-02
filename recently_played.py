import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
from prefect.blocks.system import Secret
from prefect import task, flow

secret_block = Secret.load('spotify-client-secret')
SPOTIFY_CLIENT_ID = 'fbea17b0f8344dfd8af04f8dc450842b'
SPOTIFY_CLIENT_SECRET = secret_block.get()
SPOTIFY_REDIRECT_URI = 'http://localhost:8080/callback'
SCOPE = 'user-read-recently-played'
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)

@task
def get_recently_played():
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope='user-read-recently-played'
    ))
    results = sp.current_user_recently_played(limit=10)
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

    # Convert 'played_at' to a datetime object
    df['played_at'] = pd.to_datetime(df['played_at'])
    print(df)
    return df

@flow
def print_dataframe():
    played_tracks = get_recently_played()
    df = create_dataframe(played_tracks)
    print(f"Created DataFrame with {len(df)} tracks.")
    print(df)

print_dataframe_deployment = print_dataframe.to_deployment(
    name='Create Recently Played Datafarame', cron="00 14 * * *")

