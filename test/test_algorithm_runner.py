"""
Module containing tests of the algorithm runner.

These only really make sure that the correct algorithm are being executed.
The results of directly running algorithms are compared with results
returned by the algorithm runner to make sure they're always exactly equal.
"""

from pytest import raises, mark
from unittest import TestCase
from engine.errors.user_input import UserInputError
from engine.preprocessing.module_parser import get_modules_from_dir
from engine.algorithms.oxygen.oxygen import oxygen
from engine.algorithms.chlorine.chlorine import \
    chlorine_single_repo, chlorine_two_repos
from engine.algorithms.iodine.iodine import iodine
from engine.algorithms.algorithm_runner import \
    OXYGEN, CHLORINE, IODINE, run_single_repo, run_two_repos
from test import test_repo1_dir, test_repo2_dir


class AlgorithmRunnerSingleRepoTest(TestCase):
    """Test case for single-repository mode of algorithm runner."""

    def setUp(self):
        """Load modules only from the first test repository."""
        self.modules1 = get_modules_from_dir(test_repo1_dir)

    def test_single_repo_oxygen(self):
        """Compare direct Oxygen result with the algorithm runner result."""
        direct_result = oxygen(self.modules1)
        runner_result = run_single_repo(self.modules1, OXYGEN)

        # Equality operator is not overloaded (yet), so the easiest
        # way of comparing results is using their JSON representations.
        assert direct_result.json() == runner_result.json()

    def test_single_repo_chlorine(self):
        """Compare direct Chlorine result with the algorithm runner result."""
        direct_result = chlorine_single_repo(self.modules1)
        runner_result = run_single_repo(self.modules1, CHLORINE)

        assert direct_result.json() == runner_result.json()

    def test_single_repo_iodine(self):
        """Make sure single-repo Iodine fails. It is not implemented yet."""
        with raises(UserInputError):
            run_single_repo(self.modules1, IODINE)


class AlgorithmRunnerTwoReposTest(TestCase):
    """Test case for two-repository mode of algorithm runner."""

    def setUp(self):
        """Load modules from both the first and the second test repository."""
        self.modules1 = get_modules_from_dir(test_repo1_dir)
        self.modules2 = get_modules_from_dir(test_repo2_dir)

    def test_two_repos_oxygen(self):
        """
        Make sure that running Oxygen on two repos throws an error.

        That's meant to happen because the
        functionality is not yet implemented.
        """
        with raises(UserInputError):
            run_two_repos(self.modules1, self.modules2, OXYGEN)

    def test_two_repos_chlorine(self):
        """Compare direct Chlorine result with the algorithm runner result."""
        direct_result = chlorine_two_repos(self.modules1, self.modules2)
        runner_result = run_two_repos(self.modules1, self.modules2, CHLORINE)

        assert direct_result.json() == runner_result.json()

    # NOTE: This test is very slow, hence the "slow" PyTest mark.
    @mark.slow
    def test_two_repos_iodine(self):
        """Compare direct Iodine result with the algorithm runner result."""
        direct_result = iodine(self.modules1, self.modules2)
        runner_result = run_two_repos(self.modules1, self.modules2, IODINE)

        assert direct_result.json() == runner_result.json()
