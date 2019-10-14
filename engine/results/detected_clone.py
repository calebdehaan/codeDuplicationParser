"""Module containing the `DetectedClone` class for storing clone information."""


class DetectedClone:
    """
    Representation of a single detected code clone.

    Similarity coefficient is a floating-point number between 0 and 1,
    where 0 means the subtrees are completely different and 1 means
    the subtrees are exactly equal and contain no holes.

    Attributes:
        value {string} -- String representation common to all the nodes.
        match_weight {int} -- Weight of the matching subtree skeleton.
        origins {dict[NodeOrigin: float]} -- Origins and similarity coefficients.
                                         Origins are used for keys.
                                         Similarity coefficients are values.

    """

    def __init__(self, value, match_weight, origins=None, nodes=None):
        """
        Initialize a new detected clone given its values and origin nodes.

        It is possible to either supply a dictionary of origins
        (this is useful when recreating a detected clone instance)
        or a list of list of origin TreeNodes, which is more useful right
        after running a clone detection algorithm, which produces them.

        See class docstring for details on constructor arguments.

        Arguments:
            value {string} -- String representation common to all the nodes.
            match_weight {int} -- Weight of the matching subtree skeleton.
            origins {dict[NodeOrigin: float]} -- Origins and similarity coefficients.
                                             Origins are used for keys.
                                             Similarity coefficients are values.
            nodes {list[TreeNode]} -- List of origin nodes.

        """
        if origins is None == nodes is None:
            raise ValueError("Either origins or nodes must be non-None")

        self.value = value
        self.match_weight = match_weight
        self.origins = origins or \
            {n.origin: match_weight / n.weight for n in nodes}

    def dict(self):
        """
        Convert the detected clone into its dictionary representation.

        This is necessary for later conversion to JSON, because
        there is no easy way to tell the JSON encoder how to encode
        instances of user-defined classes.

        Returns:
            dict -- Dictionary representation of the detected clone,
                    including all of its attributes.

        """
        # HACK: Maybe there's a prettier solution.
        # This was just a quick fix to make the to-JSON conversion work.
        return {"value": self.value,
                "match_weight": self.match_weight,
                "origins": {str(k): v for k, v in self.origins.items()}}
