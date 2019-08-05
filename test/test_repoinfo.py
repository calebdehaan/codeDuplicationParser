"""Module containing unit tests for the RepoInfo class."""

from os.path import join as path_join, relpath
from engine.preprocessing.repoinfo import RepoInfo, clone_root_dir


def test_repoinfo_parse():
    """Test the RepoInfo's static method for parsing repo path."""
    info = RepoInfo.parse_repo_info("hTTpS://GiTHuB.CoM/username/repository")

    assert info is not None

    assert info.url == "https://:@github.com/username/repository"

    assert info.server == "github.com"
    assert info.user == "username"
    assert info.name == "repository"

    expected_dir = path_join("github.com", "username", "repository")
    assert relpath(info.dir, clone_root_dir) == expected_dir

    assert info.hash is None
