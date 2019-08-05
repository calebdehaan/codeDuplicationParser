"""Module containing the `RepoInfo` class."""

import re
from os.path import isdir, dirname, join as path_join
from git import Repo, InvalidGitRepositoryError, GitCommandError
from engine import __file__ as engine_base_path
from urllib.parse import urlparse, urlunparse

# Base directory for all cloned repositories is "[main module root directory]/repos/".
clone_root_dir = path_join(dirname(engine_base_path), "repos")


class RepoInfo:
    """
    Encapsulates all available information about a repository into a single object.

    Attributes:
        url {string} -- Full remote source URL of the repository.
        server {string} -- Name of the source server (e.g., "github.com").
        user {string} -- Username of the repository owner.
        name {string} -- Name of the repository on the server.
        dir {string} -- Path to the local clone of the repository.
        hash {string} -- Hash of the last pulled commit.

    """

    def __init__(self, url, server, user, name, local_dir, commit_hash=None):
        """
        Initialize a new repository information object.

        Arguments:
            url {string} -- Full remote source URL of the repository.
            server {string} -- Name of the source server (e.g., "github.com").
            user {string} -- Username of the repository owner.
            name {string} -- Name of the repository on the server.
            local_dir {string} -- Path to the local clone of the repository.
            commit_hash {string} -- Hash of the last pulled commit.

        """
        self.url = url
        self.server = server
        self.user = user
        self.name = name
        self.dir = local_dir
        self.hash = commit_hash

    def clone_or_pull(self):
        """Clone the repository or pull it if it has already been cloned."""
        try:
            # If repo dir already exists, pull it.
            if isdir(self.dir):
                repo = Repo(self.dir)
                repo.remotes.origin.pull()

            # If the repo hasn't been cloned yet, clone it.
            else:
                repo = Repo.clone_from(self.url, self.dir)

            # Get HEAD's hash and store it in repo info.
            self.hash = repo.head.object.hexsha
            return True

        except InvalidGitRepositoryError:
            return False

        except GitCommandError:
            return False

    @staticmethod
    def parse_repo_info(repo_path):
        """
        Parse repository information from a repository path.

        There are two valid repository path formats:
            - Full remote repository URL (supports both GitHub and GitLab).
                "https://github.com/user/repo"
            - Short GitHub repository URL (only works with GitHub).
                "user/repo"

        """
        try:
            parts = urlparse(repo_path)
        except ValueError:
            return None

        if parts.username or parts.password or parts.params or parts.query or \
                parts.fragment or parts.scheme not in {"https", "http", ""}:
            return None

        path_match = re.fullmatch(
            r"/*([\w\-\.]+)/*([\w\-\.]+?)(?:\.git)?/*", parts.path)

        if not path_match:
            # If there is no scheme, try to prepend HTTPS
            return None if parts.scheme else \
                RepoInfo.parse_repo_info("https://" + repo_path)

        repo_user = path_match[1]
        repo_name = path_match[2]

        scheme = parts.scheme or "https"
        server = parts.netloc or "github.com"

        server_regex = re.compile(r"^(?:www\.)?(git(?:hub|lab)\.com)$",
                                  re.IGNORECASE)

        server_match = server_regex.fullmatch(server)
        if parts.netloc and server_match:
            scheme = "https"
            server = server_match[1].lower()

        # Inserting ":@" before hostname prevents a username/password prompt.
        full_url = urlunparse((scheme, ":@" + server,
                               f"/{repo_user}/{repo_name}", "", "", ""))

        clone_dir = path_join(clone_root_dir, server, repo_user, repo_name)

        return RepoInfo(full_url, server, repo_user, repo_name, clone_dir)

    def __str__(self):
        """Convert the most useful repo info into a human-readable string."""
        info_str = f"{self.url} -> {self.dir}"

        if self.hash:
            info_str += f" (commit: {self.hash})"

        return info_str

    def __repr__(self):
        """Return string representation of the repository information."""
        return self.__str__()
