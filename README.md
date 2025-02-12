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

## Installation

1. **Clone or download this repository** (or simply download the script file).
2. **Ensure that Python 3, Git, and GitHub CLI are installed** on your system.
3. **Authenticate with GitHub CLI:**
    ```bash
    gh auth login
    ```

## Usage

The script can operate in two modes:

-   **Owner Mode:** Back up all repositories for a specified owner.
-   **Repository Mode:** Back up a single repository.

### Command-Line Arguments

-   `--repo`:  
    A single GitHub repository in the format `owner/repo` (e.g., `tact-lang/tact`).

-   `--owner`:  
    A GitHub owner (user or organization) whose repositories should be backed up (e.g., `tact-lang`).

    **Note:** Use either `--repo` or `--owner` (they are mutually exclusive).

-   `--backup-dir`:  
    **(Required)** The directory where the backups will be stored.

-   `--threads`:  
    _(Optional)_ The number of threads to use for concurrent operations (default is 10).

### Examples

#### Back Up All Repositories for an Owner

```bash
python backup_github_repos.py --owner tact-lang --backup-dir /path/to/backup --threads 10
```

This command will list all repositories for the owner `tact-lang` and back up each one into a subdirectory under `/path/to/backup`.

#### Back Up a Single Repository

```bash
python backup_github_repos.py --repo tact-lang/tact --backup-dir /path/to/backup --threads 10
```

This command will back up only the repository `tact-lang/tact` into the specified backup directory.

## Output Structure

For each repository backed up, the following directory structure is created:

```
<backup_dir>/<repo_name>/
  ├── repo/             # Git clone of the repository code
  ├── issues/           # JSON files for each issue (with comments)
  ├── pull_requests/    # JSON files for each pull request (with comments and reviews)
  └── wiki/             # Git clone of the repository’s wiki (if available)
```

## Disclaimer

This script leverages the GitHub CLI and Git to back up your repositories and is not officially affiliated with GitHub. Use it at your own risk.
