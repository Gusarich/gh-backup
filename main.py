#!/usr/bin/env python3
"""
A Python script to back up GitHub repositories including code, issues, pull requests, and wiki.

You can either:
  - Backup all repositories for a given owner (user or organization), or
  - Backup a single repository.

For example:
  Backup all repositories for owner "tact-lang":
      python backup_github_repos.py --owner tact-lang --backup-dir /path/to/backup --threads 10

  Backup a single repository "tact-lang/tact":
      python backup_github_repos.py --repo tact-lang/tact --backup-dir /path/to/backup --threads 10

This script uses the GitHub CLI (gh) API with pagination and multithreading to fetch issues and pull requests,
and uses git to clone the repository and its wiki.
"""

import argparse
import concurrent.futures
import json
import os
import subprocess


def run_command(command):
    """
    Run a subprocess command and return its stdout as a string.
    Raises a CalledProcessError if the command fails.
    """
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def backup_repository(repo, backup_dir):
    """Clone the repository code using GitHub CLI."""
    repo_backup_dir = os.path.join(backup_dir, "repo")
    if os.path.exists(repo_backup_dir):
        print(f"[Repo] Repository already cloned at {repo_backup_dir}, skipping clone.")
    else:
        print(f"[Repo] Cloning repository '{repo}' into {repo_backup_dir} ...")
        subprocess.run(["gh", "repo", "clone", repo, repo_backup_dir], check=True)
        print("[Repo] Repository clone complete.")


def backup_issue_worker(issue, owner, repo_name, issues_dir):
    """
    Worker function to back up a single issue:
      - Fetch its comments
      - Save the issue (with comments) as a JSON file.
    """
    number = issue["number"]
    issue_file = os.path.join(issues_dir, f"issue_{number}.json")
    if os.path.exists(issue_file):
        print(f"[Issues] Issue #{number} already backed up, skipping.")
        return

    print(f"[Issues] Backing up issue #{number} ...")
    try:
        comments_json = run_command(
            [
                "gh",
                "api",
                f"/repos/{owner}/{repo_name}/issues/{number}/comments?per_page=100",
            ]
        )
        comments_data = json.loads(comments_json)
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        comments_data = []
    issue["comments_data"] = comments_data

    with open(issue_file, "w", encoding="utf-8") as f:
        json.dump(issue, f, indent=2)


def backup_pull_request_worker(pr, owner, repo_name, prs_dir):
    """
    Worker function to back up a single pull request:
      - Fetch its issue comments (via the issues endpoint)
      - Fetch its reviews
      - Save the PR (with comments and reviews) as a JSON file.
    """
    number = pr["number"]
    pr_file = os.path.join(prs_dir, f"pr_{number}.json")
    if os.path.exists(pr_file):
        print(f"[PRs] Pull request #{number} already backed up, skipping.")
        return

    print(f"[PRs] Backing up pull request #{number} ...")
    try:
        comments_json = run_command(
            [
                "gh",
                "api",
                f"/repos/{owner}/{repo_name}/issues/{number}/comments?per_page=100",
            ]
        )
        comments_data = json.loads(comments_json)
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        comments_data = []
    pr["comments_data"] = comments_data

    try:
        reviews_json = run_command(
            [
                "gh",
                "api",
                f"/repos/{owner}/{repo_name}/pulls/{number}/reviews?per_page=100",
            ]
        )
        reviews_data = json.loads(reviews_json)
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        reviews_data = []
    pr["reviews"] = reviews_data

    with open(pr_file, "w", encoding="utf-8") as f:
        json.dump(pr, f, indent=2)


def backup_issues(repo, backup_dir, num_threads):
    """
    Backup all issues (excluding pull requests) using the GitHub API with pagination.
    Uses a thread pool to process individual issues concurrently.
    """
    issues_dir = os.path.join(backup_dir, "issues")
    os.makedirs(issues_dir, exist_ok=True)
    owner, repo_name = repo.split("/")
    print("[Issues] Fetching all issues (excluding pull requests) with pagination ...")

    issues_json = run_command(
        [
            "gh",
            "api",
            "--paginate",
            f"/repos/{owner}/{repo_name}/issues?state=all&per_page=100",
        ]
    )
    try:
        issues_data = json.loads(issues_json)
    except json.JSONDecodeError:
        print("Failed to parse JSON response for issues.")
        return

    # Filter out pull requests (those have a "pull_request" key)
    issues = [issue for issue in issues_data if "pull_request" not in issue]
    print(f"[Issues] Found {len(issues)} issues.")

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [
            executor.submit(backup_issue_worker, issue, owner, repo_name, issues_dir)
            for issue in issues
        ]
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print("Error processing an issue:", e)

    print("[Issues] Issue backup complete.")


def backup_pull_requests(repo, backup_dir, num_threads):
    """
    Backup all pull requests using the GitHub API with pagination.
    Uses a thread pool to process individual pull requests concurrently.
    """
    prs_dir = os.path.join(backup_dir, "pull_requests")
    os.makedirs(prs_dir, exist_ok=True)
    owner, repo_name = repo.split("/")
    print("[PRs] Fetching all pull requests with pagination ...")

    prs_json = run_command(
        [
            "gh",
            "api",
            "--paginate",
            f"/repos/{owner}/{repo_name}/pulls?state=all&per_page=100",
        ]
    )
    try:
        prs = json.loads(prs_json)
    except json.JSONDecodeError:
        print("Failed to parse JSON response for pull requests.")
        return

    print(f"[PRs] Found {len(prs)} pull requests.")

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [
            executor.submit(backup_pull_request_worker, pr, owner, repo_name, prs_dir)
            for pr in prs
        ]
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print("Error processing a pull request:", e)

    print("[PRs] Pull request backup complete.")


def backup_wiki(repo, backup_dir):
    """
    Clone the wiki repository.
    GitHub wikis are separate Git repositories.
    For a repository named owner/repo, the wiki URL is:
      https://github.com/owner/repo.wiki.git
    """
    wiki_dir = os.path.join(backup_dir, "wiki")
    owner, repo_name = repo.split("/")
    wiki_repo_url = f"https://github.com/{owner}/{repo_name}.wiki.git"
    if os.path.exists(wiki_dir):
        print(f"[Wiki] Wiki already cloned at {wiki_dir}, skipping clone.")
    else:
        print(f"[Wiki] Cloning wiki from {wiki_repo_url} into {wiki_dir} ...")
        subprocess.run(["git", "clone", wiki_repo_url, wiki_dir], check=True)
        print("[Wiki] Wiki clone complete.")


def backup_all(repo, backup_dir, num_threads):
    """
    Run all backup steps for a given repository.
    This includes:
      - Cloning the repository code.
      - Backing up issues and pull requests (with pagination and multithreading).
      - Cloning the wiki.
    """
    os.makedirs(backup_dir, exist_ok=True)
    print(f"\nStarting backup for repository '{repo}' into directory '{backup_dir}'\n")
    backup_repository(repo, backup_dir)
    backup_issues(repo, backup_dir, num_threads)
    backup_pull_requests(repo, backup_dir, num_threads)
    backup_wiki(repo, backup_dir)
    print(f"\nBackup for repository '{repo}' complete!\n")


def main():
    parser = argparse.ArgumentParser(
        description="Backup GitHub repositories (code, issues, pull requests, wiki) using GitHub CLI."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--owner",
        type=str,
        help="GitHub owner (user or organization) whose repositories should be backed up (e.g., tact-lang)",
    )
    group.add_argument(
        "--repo",
        type=str,
        help="A single GitHub repository in the format owner/repo (e.g., tact-lang/tact)",
    )
    parser.add_argument(
        "--backup-dir",
        type=str,
        required=True,
        help="Main directory where backups will be stored",
    )
    parser.add_argument(
        "--threads",
        type=int,
        default=10,
        help="Number of threads to use for concurrent operations (default: 10)",
    )
    args = parser.parse_args()
    num_threads = args.threads

    if args.owner:
        owner = args.owner
        print(f"Listing repositories for owner: {owner}")
        try:
            repos_list_json = run_command(
                [
                    "gh",
                    "repo",
                    "list",
                    owner,
                    "--limit",
                    "1000",
                    "--json",
                    "nameWithOwner",
                ]
            )
            repos = json.loads(repos_list_json)
        except Exception as e:
            print("Failed to list repositories for owner", owner, ":", e)
            return

        if not repos:
            print("No repositories found for owner", owner)
            return

        for repo_info in repos:
            full_repo_name = repo_info["nameWithOwner"]  # e.g., "tact-lang/tact"
            # Use the repository part (after the slash) for naming the backup subdirectory.
            repo_name = full_repo_name.split("/")[1]
            backup_dir_for_repo = os.path.join(args.backup_dir, repo_name)
            print(
                f"\nBacking up repository {full_repo_name} into {backup_dir_for_repo}"
            )
            try:
                backup_all(full_repo_name, backup_dir_for_repo, num_threads)
            except subprocess.CalledProcessError as e:
                print("An error occurred while backing up repository", full_repo_name)
                print("stdout:", e.stdout)
                print("stderr:", e.stderr)
    else:
        try:
            backup_all(args.repo, args.backup_dir, num_threads)
        except subprocess.CalledProcessError as e:
            print("An error occurred while backing up repository", args.repo)
            print("stdout:", e.stdout)
            print("stderr:", e.stderr)


if __name__ == "__main__":
    main()
