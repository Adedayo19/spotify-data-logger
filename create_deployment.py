from prefect import flow

SOURCE_REPO="https://github.com/Adedayo19/spotify-data-logger.git"

if __name__ == "__main__":
    flow.from_source(
        source=SOURCE_REPO,
        entrypoint="recently_played.py:update_recently_played", # Specific flow to run
    ).deploy(
        name="Spotify-deployment",
        work_pool_name="my-work-pool", # Work pool target
        cron="*/30 * * * *", # Cron schedule (every minute)
    )