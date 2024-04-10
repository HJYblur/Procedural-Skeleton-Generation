import fbx
import csv
from collections import deque
import pymel.core as pm
import maya.cmds as cmds
import maya.OpenMaya as OpenMaya
# from utils import total_vertex



class Skeleton_node:
    def __init__(self, name, parent=None, level=0, weight=0, loss=0, deleted=False):
        self.name = name
        self.parent = parent
        self.children = []
        self.level = level
        self.deleted = deleted
        self.weight = weight
        self.loss = loss
        self.ratio = 0


def clamp(value, lower_bound, upper_bound):
    return max(lower_bound, min(value, upper_bound))


def map_value(x, x_min, x_max, y_min=0, y_max=100):
    normalized_value = (x - x_min) / (x_max - x_min)
    mapped_value = y_min + (normalized_value * (y_max - y_min))
    return clamp(mapped_value, y_min, y_max)


def compute_weight(joint_name):
    skinClusters = cmds.ls(type='skinCluster')
    vertexCount = 0
    
    for cluster in skinClusters:
        geometries = cmds.skinCluster(cluster, query=True, geometry=True)
        
        for geo in geometries:
            vertices = cmds.ls(f'{geo}.vtx[*]', flatten=True)
            
            for vert in vertices:
                weights = cmds.skinPercent(cluster, vert, query=True, value=True)
                influences = cmds.skinPercent(cluster, vert, query=True, transform=None)
                
                if joint_name in influences:
                    vertexCount += 1

    print(f"So {joint_name} have {vertexCount} vertices.")
    if vertexCount == 0:
        weight = 100
    else:
        weight = map_value(vertexCount, 0, total_vertex)
    return weight


def create_skeleton_tree(fbx_node, parent_skeleton_node=None, level=0):
    root = None
    current_skeleton_node = None
    node_attribute = fbx_node.GetNodeAttribute() # 检查当前节点是否是骨骼类型
    if (
        node_attribute
        and node_attribute.GetAttributeType() == fbx.FbxNodeAttribute.eSkeleton
    ):
        node_name = fbx_node.GetName()
        node_weight = 10.0 / level
        # print(f"{node_name} have {node_weight} weight, {level} level.")
        delete_flag = False
        if level == 14: delete_flag = True
        current_skeleton_node = Skeleton_node(
            node_name, parent_skeleton_node, level, node_weight, deleted=delete_flag
        )
        if parent_skeleton_node is None:
            root = current_skeleton_node  # 如果是根骨骼节点，则记录为root
        else:
            parent_skeleton_node.children.append(current_skeleton_node)
    else:
        current_skeleton_node = parent_skeleton_node  # 维持当前父节点，以便继续向下遍历

    # 无论当前节点是否为骨骼，都继续遍历其所有子节点
    for i in range(fbx_node.GetChildCount()):
        child_result = create_skeleton_tree(
            fbx_node.GetChild(i), current_skeleton_node, level + 1
        )
        if child_result and root is None:
            root = child_result  # 如果子调用返回了根节点，则在这里捕获

    return root if parent_skeleton_node is None else None


def print_skeleton_tree(node, indent=0):
    print("    " * indent + node.name + ", level: " + str(node.level))
    for child in node.children:
        print_skeleton_tree(child, indent + 1)


# 层次遍历
def levelorder_travelsal(root):
    if not root:
        return []

    queue = deque([root])
    temp_result = []

    while queue:
        level_size = len(queue)
        current_level = []

        for _ in range(level_size):
            node = queue.popleft()
            current_level.append(node)
            for child in node.children:
                queue.append(child)

        temp_result.append(current_level)

    return temp_result[::-1]


# 将层次遍历的结果拆解，存储在一个列表中
def sort_traversal(list_of_lists):
    final_result = []
    for cur_level in list_of_lists:  # 遍历外层列表
        for item in cur_level:  # 遍历每个层次
            # print(f"Get item: {item.name}, weight: {item.weight}, loss:{item.loss}")
            final_result.append(item)
    return final_result


# 后序遍历
def postorder_traversal(root):
    stack, postorder = [root], []
    while stack:
        node = stack.pop()
        if node:
            postorder.append(node)
            stack.extend(node.children)
    return reversed(postorder)


def create_csv(csv_file_path, node_List):
    with open(csv_file_path, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["name", "weight", "loss"])
        for node in node_List:
            writer.writerow([node.name, 1.0 / node.level, 0])


def search_csv_data(search_name):
    csv_file_path = "E:/Procedural Skeleton/Test Data/test.csv"
    with open(csv_file_path, mode="r") as file:
        reader = csv.reader(file)
        next(reader)
        for row in reader:
            if row[0] == search_name:
                return row[1], row[2]

    print("Error! No matching data")


# 动态规划解法
def knapsack(nodes, threshold):
    n = len(nodes)
    dp = [[0 for _ in range(threshold + 1)] for _ in range(n + 1)]

    for i in range(1, n + 1):
        weight = nodes[i - 1].weight
        loss = nodes[i - 1].loss
        for j in range(1, threshold + 1):
            if loss <= j:
                dp[i][j] = max(dp[i - 1][j], dp[i - 1][j - loss] + weight)
            else:
                dp[i][j] = dp[i - 1][j]

    max_weight = dp[n][threshold]

    j = threshold
    for i in range(n, 0, -1):
        if dp[i][j] != dp[i - 1][j]:
            nodes[i - 1].deleted = True
            j -= nodes[i - 1].loss

    for node in nodes:
        if node.deleted:
            print("Delete: " + node.name)

    return max_weight


def construct_tree(fbx_file_path = "E:/Animation Data/batch_pass_ball_fbx/test.fbx"):
    # 初始化FBX Manager和场景
    manager = fbx.FbxManager.Create()
    scene = fbx.FbxScene.Create(manager, "Scene")

    # 加载FBX文件
    importer = fbx.FbxImporter.Create(manager, "")

    skeleton_tree_root = None
    if importer.Initialize(fbx_file_path, -1):
        importer.Import(scene)
        importer.Destroy()

        root_node = scene.GetRootNode()
        if root_node:
            skeleton_tree_root = create_skeleton_tree(root_node)
            (
                print("----Successfully Get Skeleton Root.")
                if skeleton_tree_root is not None
                else pm.error("Error constructing skeleton tree!")
            )
    else:
        pm.error("Failed to load the FBX file.")
    # print_skeleton_tree(skeleton_tree_root)
    level_order_list = levelorder_travelsal(skeleton_tree_root)
    skeleton_node_list = sort_traversal(level_order_list)
    return skeleton_node_list

    # create_csv(skeleton_node_list)

    max_weight = knapsack(skeleton_node_list, 100)
    print("Max Weight: " + str(max_weight))
    
# node_list = construct_tree()