from prefect import serve
from prefect_github import GitHubRepository
from recently_played import print_dataframe_deployment

if __name__ == "__main__":
    github_block = GitHubRepository.load("spotify-github-repo")
    serve(
        print_dataframe_deployment,
        storage=github_block,
        pause_on_shutdown=False
    )