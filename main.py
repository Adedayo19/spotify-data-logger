from prefect import serve
from recently_played import print_dataframe_deployment

if __name__ == "__main__":
    serve(
        print_dataframe_deployment,
        pause_on_shutdown=False
    )