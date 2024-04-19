import fbx
import csv
from collections import deque
from scipy.spatial import ConvexHull
import pymel.core as pm
import maya.cmds as cmds
import maya.api.OpenMaya as OpenMaya
from delete_joint_weight import refine_weights

eps = 1e-3
error_thres = 1.0

class Skeleton_node:
    def __init__(self, name, parent=None, level=0, stability = False, weight=0, loss=0, deleted=False):
        self.name = name
        self.parent = parent
        self.children = []
        self.level = level
        self.stable = stability
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

def normalization(x, x_min=0, x_max=1):
    return (x-x_min)/(x_max-x_min)

def compute_vtx_num(joint_name):
    from utils import total_vertex
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


def compute_vtx_volumn(joint_name):
    joint = pm.PyNode(joint_name)
    
    skin_clusters = joint.listConnections(type="skinCluster", source=False)
    if not skin_clusters: #根本没有绑定的点
        return 1.0
    vtx_position = []
    
    for skin_cluster in skin_clusters:
        # influences = skin_cluster.influenceObjects()
        influences = pm.skinCluster(skin_cluster, query=True, influence=True)
        if joint not in influences:
            continue
            # raise RuntimeError(f"Can't find the {joint}.")
        
        joint_index = influences.index(joint)
        geometry = skin_cluster.getGeometry()[0]
        weights = skin_cluster.getWeights(geometry)
        weights = list(weights)
        
        vtxs_indices = [i for i, w in enumerate(weights) if w[joint_index] > 0]
        vertices_world_position = [geometry.vtx[i].getPosition(space='world') for i in vtxs_indices]
    
        vtx_position += vertices_world_position
    # print(vtx_position)
    if len(vtx_position) < 4: #绑定的顶点数目小于4，无法计算空间大小。
        return 5.0
        
    hull = ConvexHull(vtx_position)
    volumn = hull.volume
    return volumn
    

def create_skeleton_tree(fbx_node, parent_skeleton_node=None, level=0):
    root = None
    current_skeleton_node = None
    stable_list = ["FBX_C_Reference", "FBX_Basketball", "Ball_Root", "FBX_C_Hips", "FBX_R_Pelvis0", "FBX_L_Shoulder0", "FBX_R_Shoulder0"]
    node_attribute = fbx_node.GetNodeAttribute() # 检查当前节点是否是骨骼类型
    if (
        node_attribute
        and node_attribute.GetAttributeType() == fbx.FbxNodeAttribute.eSkeleton
    ):
        node_name = fbx_node.GetName()
        node_weight = compute_vtx_volumn(node_name)
        # print(f"{node_name} have {node_weight} weight.")
        stability = True if node_name in stable_list else False
        current_skeleton_node = Skeleton_node(
            node_name, parent_skeleton_node, level, stability, node_weight
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


def cp_transform(tra_A, tra_B, rot_A, rot_B):
    tran_sub = [abs(a - b) for a, b in zip(tra_A, tra_B)]
    flag = all(dimention<eps for dimention in tran_sub)
    if flag: # 表示translation没有改变
        rot_sub = [abs(a - b) for a, b in zip(rot_A, rot_B)]
        flag = all(dimention<error_thres for dimention in rot_sub)
        return flag # 表示rotation在可控范围内
    else: return flag


def extract_joint_data(joint_name, start_time, end_time):
    if not cmds.ls(joint_name, type = "joint"):
        cmds.warning(f"No joint {joint_name} found in the scene.")
        return {}
    
    cmds.currentTime(start_time)
    prev_tran = cmds.getAttr(f"{joint_name}.translate")[0]
    prev_rot  = cmds.getAttr(f"{joint_name}.rotate")[0]
    
    for frame in range(start_time+1, end_time+1):
        cmds.currentTime(frame)
    
        cur_tran = cmds.getAttr(f"{joint_name}.translate")[0] # 查到的是相较于父节点的局部变化，如果要全局变化需要设置 worldSpace=True
        cur_rot = cmds.getAttr(f"{joint_name}.rotate")[0]
        
        # print(f"{cur_tran}, {prev_tran}, {cur_rot}, {prev_rot}")
        if cp_transform(prev_tran, cur_tran, prev_rot, cur_rot):
            prev_tran = cur_tran
            prev_rot = cur_rot
            continue
        else:
            return False
    return True


def extract_all_joint_data(root):
    start_time = int(pm.playbackOptions(query=True, minTime=True))
    end_time = int(pm.playbackOptions(query=True, maxTime=True))
    node_list = postorder_traversal(root)
    for node in node_list:
        if node.stable: 
            # print(node.name + " is stable.")
            continue
        if extract_joint_data(node.name, start_time, end_time):
            node.deleted = True
            refine_weights(node.name)
            # print(node.name+" can be deleted.")
    return


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
    return skeleton_tree_root, skeleton_node_list

    # create_csv(skeleton_node_list)
    
    

# 动态规划解法(暂时废弃)
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

