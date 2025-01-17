
class Block:
    def __init__(self, parent_block):
        self.parent_block = parent_block

class Node:
    def __init__(self, block, parent, is_latest, score=0, children=None):
        if children is None:
            self.children = set()
        else:
            self.children = children
        self.block = block
        self.parent = parent
        self.is_latest = is_latest
        self.score = score

    def size(self):
        size = 1
        for child in self.children:
            size += child.size()
        return size


class CompressedTree:
    def __init__(self, genesis):
        node = Node(genesis, None, True)
        self.root = node
        self.latest_block_nodes = dict()

    def block_in_tree(self, block):
        def block_below_node(block, node):
            if node.block == block:
                return True
            for child in node.children:
                if block_below_node(block, child):
                    return True
            return False
        return block_below_node(block, self.root)

    def node_with_block(self, block, node):
        if node.block == block:
            return node
        for child in node.children:
            node = self.node_with_block(block, child)
            if node is not None:
                return node
        return None

    def find_prev_in_tree(self, block):

        curr = block
        while not self.block_in_tree(curr):
            curr = curr.parent_block

        return self.node_with_block(curr, self.root)

    def find_lca_block(self, block_1, block_2):
        curr_block_1 = block_1
        while curr_block_1 is not None:
            curr_block_2 = block_2
            while curr_block_2 is not None:
                if curr_block_1 == curr_block_2:
                    return curr_block_1
                curr_block_2 = curr_block_2.parent_block
            curr_block_1 = curr_block_1.parent_block

        raise AssertionError("Fuuuuuck")

    def add_new_latest_block(self, block, validator):
        new_node = self.add_block(block)

        if validator in self.latest_block_nodes:
            old_node = self.latest_block_nodes[validator]
            self.remove_node(old_node)

        self.latest_block_nodes[validator] = new_node
        return new_node

    def add_block(self, block):
        prev_in_tree = self.find_prev_in_tree(block)
        if len(prev_in_tree.children) == 0:
            node = Node(block, prev_in_tree, is_latest=True)
            prev_in_tree.children.add(node)
            return node
        for child in prev_in_tree.children:
            ancestor = self.find_lca_block(block, child.block)
            if ancestor != prev_in_tree.block:
                # haven't made the ancestor node, yet
                node = Node(block, None, is_latest=True)
                anc_node = Node(ancestor, prev_in_tree, children={node, child}, is_latest=False)
                # update the node's parent pointer
                node.parent = anc_node
                prev_in_tree.children.add(anc_node)
                prev_in_tree.children.remove(child)
                return node
        # insert on the prev_in_tree
        node = Node(block, prev_in_tree, True)
        prev_in_tree.children.add(node)
        return node

    def size(self):
        return self.root.size()

    def remove_node(self, node):
        num_children = len(node.children)
        if num_children > 1:
            node.is_latest = False
        elif num_children == 1:
            child = node.children.pop()
            child.parent = node.parent
            node.parent.children.remove(node)
            node.parent.children.add(child)
        else:
            parent = node.parent
            parent.children.remove(node)
            del(node)
            if not parent.is_latest and len(parent.children) == 1:
                par_child = parent.children.pop()
                par_child.parent = parent.parent
                parent.parent.children.remove(parent)
                parent.parent.children.add(par_child)
                del(parent)


# Some light tests

def test_inserting_on_genesis():
    genesis = Block(None)
    tree = CompressedTree(genesis)

    block = Block(genesis)
    node = tree.add_new_latest_block(block, 0)

    assert tree.size() == 2
    assert tree.root.block == genesis
    assert tree.root.children.pop() == node


def test_inserting_on_leaf():
    genesis = Block(None)
    tree = CompressedTree(genesis)

    block_1 = Block(genesis)
    node_1 = tree.add_new_latest_block(block_1, 0)

    block_2 = Block(block_1)
    node_2 = tree.add_new_latest_block(block_2, 0)

    assert tree.size() == 2
    assert tree.root.block == genesis
    assert tree.root.children.pop() == node_2

def test_inserting_on_intermediate():
    genesis = Block(None)
    tree = CompressedTree(genesis)

    block_1 = Block(genesis)
    node_1 = tree.add_new_latest_block(block_1, 0)

    block_2 = Block(block_1)
    node_2 = tree.add_new_latest_block(block_2, 0)

    on_inter_block = Block(block_1)
    on_inter_node = tree.add_new_latest_block(on_inter_block, 1)

    assert tree.size() == 4
    assert tree.root == on_inter_node.parent.parent

def test_vals_add_on_other_blocks():
    genesis = Block(None)
    tree = CompressedTree(genesis)

    for i in range(3):
        block = Block(genesis)
        node = tree.add_new_latest_block(block, i)

    val_0_block = tree.latest_block_nodes[0].block
    for i in range(3):
        block = Block(val_0_block)
        node = tree.add_new_latest_block(block, i)

    assert tree.size() == 5


if __name__ == "__main__":
    print("Running tests...")
    test_inserting_on_genesis()
    test_inserting_on_leaf()
    test_inserting_on_intermediate()
    test_vals_add_on_other_blocks()
    print("All tests passed!")
