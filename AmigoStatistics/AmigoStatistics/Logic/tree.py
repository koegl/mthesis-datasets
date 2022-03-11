class Tree(object):
    """Generic tree node."""
    def __init__(self, name="root", children=None, sh_id=None, vtk_id=None):

        self.name = name

        self.children = {}
        if children is not None:  # todo what does this do?
            for child in children:
                self.add_child(child)

        self.sh_id = sh_id
        self.vtk_id = vtk_id

        self.parent = None

        self.sh_study_id = None  # not to which sh_study the node belongs, but which sh_study was created from it
        self.dcm_series_instance_uid = None

    def __repr__(self):
        return self.name

    def add_child(self, node):
        assert isinstance(node, Tree)
        self.children[node.name] = node
        self.children[node.name].parent = self
        return node

    def remove_child(self, name):
        assert isinstance(name, str)
        assert name in self.children

        self.children.pop(name)

    def root(self):

        if self.parent is None:
            return self

        parent = self.parent

        while parent is not None:
            if parent.parent is None:
                return parent
            else:
                parent = parent.parent

    @staticmethod
    def bfs(node):
        """
        DFS on a node, returns nodes in BFS order
        @param node: The root of the (sub-) tree
        @return: List of nodes
        """
        assert isinstance(node, Tree), "Node is not a Tree"

        # array with visited and FIFO queue with nodes
        visited = [node.sh_id]
        return_array = []
        q = [node]

        while q:
            s = q.pop(0)

            for child_name, child in s.children.items():
                if child.sh_id not in visited:
                    q.append(child)
                    visited.append(child.sh_id)
                    return_array.append(child)

        return return_array
