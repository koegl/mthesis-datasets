class Tree(object):
    """Generic tree node."""
    def __init__(self, name="root", children=None, id=None):

        self.name = name

        self.children = {}
        if children is not None:
            for child in children:
                self.add_child(child)

        self.id = id

        self.parent = None

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



