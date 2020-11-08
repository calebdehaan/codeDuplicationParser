from bitstring import BitArray
from .pattern_clustering import clustering
from .anti_unification import anti_unify
import os

# Minimum weight of a single node used in comparison.
_MIN_NODES = int(os.environ["IODINE_MIN_NODES"]) or 20
_MAX_HOLES = int(os.environ["IODINE_MAX_HOLES"]) or 10
_HOLE_MASS_LIMIT = int(os.environ["IODINE_HOLE_MASS_LIMIT"]) or 5


def pattern_collection(tree_list_1, tree_list_2):
    """
    Compare two Abstract Syntax Trees representing two methods. The trees are
    provided as lists to provides indexes for the nodes within the tree.

    Arguments:
        tree_list_1 {list[TreeNode]}: A TreeNode tree represented as a list
        tree_list_2 {list[TreeNode]}: A TreeNode tree represented as a list

    Returns:
        list[list[PatternNode]]: The clustered patterns identified in the repositories

    """
    # Get the sizes of the trees
    size_tree_1 = len(tree_list_1)
    size_tree_2 = len(tree_list_2)

    # Checks whether a pairing has been compared. Set all to false (0) originally
    bit_string = '0b' + ('0' * len(tree_list_2))
    work_list = [BitArray(bit_string) for _ in tree_list_1]

    # sets of minimum common subtrees (patterns) of trees
    pats = [[] for i in range(size_tree_1)]
    # sets of patterns which have been clustered together
    cpats = []

    # for all subtrees of both trees
    for i in range(size_tree_1):
        for j in range(size_tree_2):
            # if neither tree is a leaf node and the pair hasn't been checked
            if tree_list_1[i].children and tree_list_2[j].children and work_list[i].all(False, [j]):
                # we have now checked this pairing
                work_list[i].set(True, j)
                # if the root nodes of the subtrees are equal
                if tree_list_1[i] == tree_list_2[j]:
                    # Check our parameters
                    pat, num_holes, max_hole_size = anti_unify(tree_list_1, tree_list_2, i, j, work_list)
                    if pat.get_match_weight() >= _MIN_NODES and num_holes >= _MAX_HOLES \
                            and max_hole_size <= _HOLE_MASS_LIMIT:
                        # Add the results of anti-unify to the list of subtrees
                        pats[i].append(pat)
    # for every set of patterns (one per node in the first tree)
    for pattern_set in pats:
        # run the clustering function on the pattern set
        cpats.append(clustering(pattern_set))
    # Return the sets of clustered patterns
    return cpats
