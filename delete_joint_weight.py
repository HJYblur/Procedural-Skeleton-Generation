import pymel.core as pm
import datetime
import json

def save_log(joint_name, removed_weights_info):
    
    current_maya_file = pm.sceneName().basename().split('.')[0]
    current_time = datetime.datetime.now().strftime("%m%d-%H%M")

    log_file_name = f"{current_maya_file}_{joint_name}_{current_time}.txt"

    parent_path = "E:/Procedural Skeleton/Log/Skeleton Reduction/"
    log_file_path = parent_path + log_file_name

    with open(log_file_path, 'w') as log_file:
        
        for vtx_name, joints in removed_weights_info:
            info_str = f"Removed weights from {vtx_name} for joints: {', '.join(joints)}"
            print(info_str)
            log_file.write(info_str + '\n')

    print(f"Log saved to: {log_file_path}")


def export_weight(file_path="E:/Procedural Skeleton/Log/Joint Weight Restoration/weights.json"):
    import json
    import pymel.core as pm
    
    skin_clusters = pm.ls(typ="skinCluster")
    all_weights_dict = {}
    for skin in skin_clusters:
        geos = pm.skinCluster(skin, query=True, geometry=True)
        influences = pm.skinCluster(skin, query=True, influence=True)
        
        for geo in geos:
            weights_dict = {}
            for inf in influences:
                # 获取几何体的所有顶点
                vtxs = pm.ls(geo + ".vtx[*]", flatten=True)
                weights = [pm.skinPercent(skin, vtx, transform=inf, query=True) for vtx in vtxs]
                weights_dict[str(inf)] = weights
            all_weights_dict[str(skin)] = weights_dict
        
    with open(file_path, "w") as file:
        json.dump(all_weights_dict, file, indent=4)

        
        
def import_weights(file_path="E:/Procedural Skeleton/Log/Joint Weight Restoration/weights.json"):
    with open(file_path, 'r') as file:
        all_weights_dict = json.load(file)
    
    for skin_cluster_name, weights_dict in all_weights_dict.items():
        skin_cluster = pm.PyNode(skin_cluster_name)
        geometry = pm.skinCluster(skin_cluster, query=True, geometry=True)
        
        for inf, weights in weights_dict.items():
            # 将字符串转换回 PyNode
            influence = pm.PyNode(inf)
            pm.skinPercent(skin_cluster, geometry, transformValue=[(influence, w) for w in weights])


def delete_weights():
    skin_clusters = pm.ls(typ="skinCluster")
    for skin_cluster in skin_clusters:
        pm.delete(skin_cluster)

    
def refine_weights(*args):
    # import_weights()
    skeleton_joints = list(args)
    weights_backup = {}  # 用于保存原始权重信息
    removed_weights_info = []  # To store information about removed weights
    
    for mesh in pm.ls(geometry=True):
        # Find the skinCluster attached to the mesh
        skinClusters = pm.listHistory(mesh, type='skinCluster')
        if not skinClusters:
            # print(f"未找到 {mesh} 的蒙皮簇。")
            continue
        
        skinCluster = skinClusters[0]
        
        # Get all influences for the skinCluster
        influences = pm.skinCluster(skinCluster, query=True, influence=True)
        
        influences_to_remove = [inf for inf in influences if inf.name() in skeleton_joints]
        if not influences_to_remove:
            # print(f"在 {skinCluster} 中未找到要移除的权重。")
            continue
        
        for vtx in mesh.vtx:
            # Check if the vertex is influenced by any joint to be removed
            weights = pm.skinPercent(skinCluster, vtx, query=True, value=True)
            influenceIndices = pm.skinPercent(skinCluster, vtx, query=True, transform=None)
            
            vtx_weights = []
            for inf, weight, _ in zip(influences, weights, influenceIndices):
                if inf in influences_to_remove and weight > 0:
                    vtx_weights.append((inf.name(), weight))
                    try:
                        pm.skinPercent(skinCluster, vtx, transformValue=[(inf.name(), 0)], normalize=True)
                    except RuntimeError as e:
                        print(f"处理 {vtx.name()} 时发生错误：{e}")

                    removed_weights_info.append((vtx.name(), [inf.name() for inf in influences_to_remove]))
            if vtx_weights:
                weights_backup[vtx.name()] = vtx_weights
        
    # save_log(skeleton_joints[0], removed_weights_info)
    
    return weights_backup


def restore_weights(weights_backup):
    for vtx_name, weights in weights_backup.items():
        vtx = pm.PyNode(vtx_name)
        geometry = vtx.node()
        his = pm.listHistory(geometry)
        skinClusters = pm.ls(his, type="skinCluster")
        skinCluster = skinClusters[0] if skinClusters else None
        for inf_name, weight in weights:
            if not pm.objExists(inf_name):
                print(f"骨骼 {inf_name} 不存在。")
                continue

            try:
                pm.skinPercent(skinCluster, vtx, transformValue=[(inf_name, weight)], normalize=True)
            except RuntimeError as e:
                print(f"尝试对 '{vtx_name}' 设置权重时发生错误: {e}")



# skeleton_joints = ['FBX_R_FingerC2'] 

# delete_weights(skeleton_joints)
# export_weight()
