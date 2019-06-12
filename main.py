
class Block:
    def __init__(self, parent_block):
        self.parent_block = parent_block


class Node:
    def __init__(self, block, parent, is_latest, score=0, children=None, child_block_to_child=None):
        if children is None:
            self.children = set()
            self.child_block_to_child = dict()
        else:
            self.children = children
            self.child_block_to_child = child_block_to_child

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

    # returns both the first node in the tree found behind the prevblock pointer of block
    # and the child block of that nodes' block with which it agrees
    def find_prev_in_tree(self, block):
        # Return the node, that contains the block, that is the highest block that is a previous block of block

        prev_block = block
        curr = block
        while not self.block_in_tree(curr):
            prev_block = curr
            curr = curr.parent_block

        # get the node that contains this block
        return self.node_with_block(curr, self.root), prev_block

    # returns the "latest common ancestor" or latest agreed upon block between blocks b1 and b2
    # and also the children of that block from the chains of the two b1 and b2, respectively
    def find_lca(self, block_1, block_2):
        prev_block_1 = block_1
        curr_block_1 = block_1
        while curr_block_1 is not None:
            prev_block_2 = block_2
            curr_block_2 = block_2
            while curr_block_2 is not None:
                if curr_block_1 == curr_block_2:
                    return curr_block_1, prev_block_1, prev_block_2
                prev_block_2 = curr_block_2
                curr_block_2 = curr_block_2.parent_block
            prev_block_1 = curr_block_1
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
        prev_in_tree, pit_child_block = self.find_prev_in_tree(block)
        if len(prev_in_tree.children) == 0:
            node = Node(block, prev_in_tree, is_latest=True)
            prev_in_tree.children.add(node)
            prev_in_tree.child_block_to_child[node] = pit_child_block
            return node
        if pit_child_block in prev_in_tree.child_block_to_child:
            ancestor, blocks_child_of_ancestor, pit_child_of_ancestor = self.find_lca(block, prev_in_tree.child_block_to_child[pit_child_block])
            node = Node(block, ancestor, is_latest=True)
            anc_node = Node(ancestor, prev_in_tree, children={node, child}, is_latest=False, child_block_to_child={pit_child_of_ancestor : child, blocks_child_of_ancestor : node})
            prev_in_tree.children.add(anc_node)
            prev_in_tree.child_block_to_child[pit_child_block] = anc_node
            prev_in_tree.children.remove(child)
            return node
        # insert on the prev_in_tree
        node = Node(block, prev_in_tree, True)
        prev_in_tree.children.add(node)
        prev_in_tree.child_block_to_child[node] = pit_child_block
        
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



if __name__ == "__main__":
    genesis = Block(None)
    tree = CompressedTree(genesis)
    print(tree.root.children)

    for i in range(3):
        block_1 = Block(genesis)
        node_1 = tree.add_new_latest_block(block_1, i)
        print("After val {} added {}, size of tree is {}".format(i, node_1, tree.size()))
        block_2 = Block(block_1)
        node_2 = tree.add_new_latest_block(block_2, i)
        print("After val {} added {}, size of tree is {}".format(i, node_2, tree.size()))
        assert tree.latest_block_nodes[i].block == block_2

    val_0_block = tree.latest_block_nodes[0].block
    for i in range(3):
        block = Block(val_0_block)
        node = tree.add_new_latest_block(block, i)
        print("After val {} added {}, size of tree is {}".format(i, node, tree.size()))
        print("Root children: {}".format(tree.root.children))


    print(tree.root.children.pop().children)