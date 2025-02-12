# GitHub Repository Backup Script

This Python script allows you to back up GitHub repositories—including the repository code, issues, pull requests, and wiki content—using the GitHub CLI (`gh`) and Git. You can use the script to back up a single repository or all repositories under a given owner (user or organization).

## Features

-   **Repository Code:**  
    Clones the repository code using `gh repo clone`.

-   **Issues Backup:**  
    Fetches all issues (excluding pull requests) with pagination and stores each issue (along with its comments) as a JSON file.

-   **Pull Requests Backup:**  
    Retrieves all pull requests with pagination and saves each pull request (with its comments and reviews) as a JSON file.

-   **Wiki Backup:**  
    Clones the repository's wiki (if available) since GitHub wikis are separate Git repositories.

-   **Multithreading:**  
    Uses Python's multithreading to process issues and pull requests concurrently. The number of threads is configurable via a CLI argument.

-   **Flexible Mode:**  
    Backup a single repository or all repositories for a given owner.

## Prerequisites

-   **Python 3.6+**
-   **GitHub CLI (`gh`):**  
    [Installation Instructions](https://cli.github.com/)
-   **Git**
-   **GitHub Authentication:**  
    Ensure you're authenticated with GitHub CLI by running:
    ```bash
    gh auth login
    ```
