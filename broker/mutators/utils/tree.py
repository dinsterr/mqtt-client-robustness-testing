class TreeNode:
    def __init__(self, v=None):
        self.data = v
        self.childs = []


def is_leaf_list(node_list):
    if isinstance(node_list, dict):
        return False
    else:
        return True


def dict2tree(dic_json):
    ret = []
    if isinstance(dic_json, list):
        for dic_json_item in dic_json:
            for key, value in dic_json_item.items():
                root = TreeNode()
                if isinstance(value, dict):
                    root.data = key
                    root.childs += dict2tree(value)
                else:
                    root.data = (key, value)
                ret.append(root)
    else:
        for key, value in dic_json.items():
            root = TreeNode()
            if isinstance(value, dict):
                root.data = key
                root.childs += dict2tree(value)
            else:
                root.data = (key, value)
            ret.append(root)
    return ret


def tree2dict(root):
    ret = {}
    if not root:
        return ret
    if isinstance(root, list):
        for key in root:
            if isinstance(key.data, tuple):
                ret[key.data[0]] = key.data[1]
            else:
                ret[key.data] = tree2dict(key.childs)
    if isinstance(root, TreeNode):
        key = root.data
        ret[key] = tree2dict(root.childs)
    return ret


def traverse(node, tree, callback):
    if not node:
        return
    if isinstance(node, TreeNode):
        if isinstance(node.data, tuple):
            callback(node, tree)
            return
        for child in node.childs:
            traverse(child, tree, callback)
        return
    if isinstance(node, list):
        for element in node:
            traverse(element, tree, callback)
