"""
Requires GhApi to run: https://pypi.org/project/ghapi/

Install via pip:
- pip install ghapi
"""

import os
from ghapi.core import GhApi
from ghapi.page import paged

# TODO: Automatically assign issue to column in project board. May involve
# looping over cards in each column on the project board instead of using
# GhApi.issues.list_for_repo. Achieved manually for now.
# See https://github.com/2i2c-org/team-compass/blob/main/scripts/post-team-sync.py
# for example.

# TODO: Also copy across any/all comments made on issues

def get_labels_for_repo(
    api: GhApi,
    owner: str = "sgibson91",
    repo: str = "open-practices-toolkit"
) -> None:
    """Return a list of label names available in a given repository

    Args:
        api (GhApi): An instatiation of GhApi
        owner (str, optional): The account the repo belongs to.
            Defaults to "sgibson91".
        repo (str, optional): The name of the repo to list issue labels for.
            Defaults to "open-practices-toolkit".

    Returns:
        (list): A list of label names that exist in the defined repo.
    """
    resps = api.issues.list_labels_for_repo(owner, repo)
    return [resp.name for resp in resps]


def create_label_for_repo(
    api: GhApi,
    label_dict: dict,
    owner: str = "sgibson91",
    repo: str = "open-practices-toolkit"
) -> None:
    """Create an issue label in a given repository

    Args:
        api (GhApi): An instantiation of GhApi
        label_dict (dict): A dictionary describing the label to create. Fields
            are: "name", the label name; "color", the label color (in hex);
            "description", the label description.
        owner (str, optional): the account the repo belongs to.
            Defaults to "sgibson91".
        repo (str, optional): The name of the repo to create the issue label for.
            Defaults to "open-practices-toolkit".
    """
    api.issues.create_label(
        owner,
        repo,
        name=label_dict["name"],
        color=label_dict["color"],
        description=label_dict["description"]
    )


def create_issue(
    api: GhApi,
    title: str,
    body: str,
    labels: list,
    owner: str = "sgibson91",
    repo: str = "open-practices-toolkit"
) -> None:
    """Create an issue in a given repository

    Args:
        api (GhApi): An instantiation of GhApi
        title (str): The title of the issue to be created
        body (str): The body of the issue to be created
        labels (list): A list of label names to assign to the issue
        owner (str, optional): The account the repo belongs to.
            Defaults to "sgibson91".
        repo (str, optional): The name of the repo to create the issue in.
            Defaults to "open-practices-toolkit".
    """
    api.issues.create(owner, repo, title=title, body=body, labels=labels)


def main():
    # Read in token from environment
    token = os.environ["GITHUB_TOKEN"] if "GITHUB_TOKEN" in os.environ else None

    if token is None:
        raise ValueError(
            "GITHUB-TOKEN is required to continue"
        )

    # Initialise GhApi
    api = GhApi(token=token)

    # Find project board details from old project
    ossa_project_board = api.projects.list_for_repo(
        "alan-turing-institute", "OpenSourceSA"
    )[0]
    ossa_project_id = ossa_project_board.id
    ossa_project_columns = api.projects.list_columns(ossa_project_id)
    ossa_project_columns = [column.name for column in ossa_project_columns]

    # Create project with matching details in new project
    api.projects.create_for_repo(
        "sgibson91",
        "open-practices-toolkit",
        name=ossa_project_board.name,
        body=ossa_project_board.body
    )
    optk_project_board = api.projects.list_for_repo(
        "sgibson91", "open-practices-toolkit"
    )
    optk_project_id = optk_project_board[0].id
    for column in ossa_project_columns:
        api.projects.create_column(optk_project_id, name=column)

    # Get labels from new repo
    labels = get_labels_for_repo(api)

    # Get pages of issues from old repo
    pages = paged(
        api.issues.list_for_repo, "alan-turing-institute", "OpenSourceSA"
    )

    # Loop through pages and issues
    for p in pages:
        for item in p:
            # Create dictionary of labels associated with current issue
            issue_labels = [
                {
                    "name": label.name,
                    "color": label.color,
                    "description": label.description
                } for label in item.labels
            ]

            # If label doesn't exist in new repo, create it and update label list
            for label in issue_labels:
                if label["name"] not in labels:
                    create_label_for_repo(api, label)
                    labels = get_labels_for_repo(api)

            # Create copy of issue in new repo
            create_issue(
                api,
                item.title,
                item.body,
                [label["name"] for label in issue_labels]
            )


if __name__ == "__main__":
    main()
