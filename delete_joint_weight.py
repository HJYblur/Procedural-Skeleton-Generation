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
    skeleton_joints = list(args)
    weights_backup = {}  # 用于保存原始权重信息
    removed_weights_info = []  # 记录移除的权重信息
    
    for mesh in pm.ls(geometry=True):
        skinClusters = pm.listHistory(mesh, type='skinCluster')
        if not skinClusters:
            # print(f"未找到 {mesh} 的蒙皮簇。")
            continue
        
        skinCluster = skinClusters[0]
        
        # In query mode, returns a string array of the influence objects (joints and transform).
        influences = pm.skinCluster(skinCluster, query=True, influence=True)
        influences_to_remove = [inf for inf in influences if inf.name() in skeleton_joints]
        if not influences_to_remove:
            # print(f"在 {skinCluster} 中未找到要移除的骨骼。")
            continue
        
        for vtx in mesh.vtx:
            # Check if the vertex is influenced by any joint to be removed
            weights = pm.skinPercent(skinCluster, vtx, query=True, value=True)
            vtx_weights_to_remove = [(weight, inf) for inf, weight in zip(influences, weights) if inf in influences_to_remove and weight>0]
            if not vtx_weights_to_remove: continue
            
            for weight, inf in vtx_weights_to_remove:
                parent_inf = pm.listRelatives(inf, parent=True)
                if not parent_inf: continue
                
                parent_inf = parent_inf[0]
                
                if vtx.name() not in weights_backup:
                    weights_backup[vtx.name()] = []
                    
                if parent_inf.name() in influences:
                    current_parent_weight = pm.skinPercent(skinCluster, vtx, transform=parent_inf, query=True)
                    new_parent_weight = current_parent_weight + weight
                    pm.skinPercent(skinCluster, vtx, transformValue=[(inf.name(), 0), (parent_inf.name(), new_parent_weight)], normalize=True)
                    removed_weights_info.append((vtx.name(), inf.name(), parent_inf.name(), weight, current_parent_weight))
                    weights_backup[vtx.name()].append((inf.name(), parent_inf.name(), weight, current_parent_weight))
                else:
                    pm.skinPercent(skinCluster, vtx, transformValue=[(inf.name(), 0)], normalize=True)
                    removed_weights_info.append((vtx.name(), inf.name(), "", weight, 0))
                    weights_backup[vtx.name()].append((inf.name(), "", weight, 0))
    # save_log(skeleton_joints[0], removed_weights_info)
    
    return weights_backup


def restore_weights(weights_backup):
    for vtx_name, weights_info_list in weights_backup.items():
        vtx = pm.PyNode(vtx_name)
        geometry = vtx.node()
        his = pm.listHistory(geometry)
        skinClusters = pm.ls(his, type="skinCluster")
        skinCluster = skinClusters[0] if skinClusters else None
        for inf_name, parent_inf_name, weight, parent_weight in weights_info_list:
            if not pm.objExists(inf_name):
                print(f"骨骼 {inf_name} 不存在。")
                continue
            if parent_inf_name=="": 
                pm.skinPercent(skinCluster, vtx, transformValue=[(inf_name, weight)], normalize=True)
            else:
                pm.skinPercent(skinCluster, vtx, transformValue=[(inf_name, weight), (parent_inf_name, parent_weight)], normalize=True)



# skeleton_joints = ['FBX_R_FingerC2'] 

# delete_weights(skeleton_joints)
# export_weight()
