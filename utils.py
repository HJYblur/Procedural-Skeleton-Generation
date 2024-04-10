import pymel.core as pm

eps = 1e-5

def count_skeleton():
    # 使用ls命令列出场景中所有的骨骼节点
    skeletons = pm.ls(type='joint')
    # 计算骨骼的数量
    skeleton_count = len(skeletons)
    print(f"Total skeletons in the scene: {skeleton_count}")
    return skeleton_count
    

def check_weight():
    lod_model_name = "LOD1"

    # 获取LOD模型绑定的骨骼
    skinClusters = pm.listHistory(lod_model_name, type='skinCluster')
    if skinClusters:
        influences = pm.skinCluster(skinClusters[0], query=True, influence=True)
        print(f"LOD Model {lod_model_name} is bound to the following joints: {influences}")
    else:
        print(f"LOD Model {lod_model_name} does not seem to be bound to any joints.")


def count_vertex():
    total_cnt= 0
    for mesh in pm.ls(type='mesh', geometry=True):
        # Check if the geometry is a mesh
        if isinstance(mesh, pm.nodetypes.Mesh) or 'mesh' in mesh.type():
            cnt = 0
            for vtx in mesh.vtx:
                cnt += 1
            total_cnt += cnt
            # print(f"{cnt} vertices in {mesh.name()}")
        else:
            # print(f"Skipping {mesh.name()} as it is not a mesh.")
            pass
    total_cnt /= 2
    print(f"total: {total_cnt} vtx.")
    return total_cnt
    # total_vertices = 0
    # for shape in pm.ls(type='mesh'):
    #     total_vertices += shape.numVertices
    # return total_vertices
    
    
def check_vtx(vtx_name, check = False):
    skinClusters = pm.listHistory(vtx_name, type='skinCluster')
    if skinClusters:
        skinCluster = skinClusters[0]
        
        influences = pm.skinCluster(skinCluster, query=True, influence=True)
        weights = pm.skinPercent(skinCluster, vtx_name, query=True, value=True)
        
        total_weight = 0
        # 打印权重分配信息
        for inf, weight in zip(influences, weights):
            if weight > 0: 
                print(f"{inf.name()}: {weight}")
                if check: total_weight+=weight
        if check and abs(total_weight-1)>eps: print(f"Error with weight normalization, current weight sum: {total_weight}")
    else:
        print(f"No skinCluster found for {vtx_name}")
    

total_vertex = count_vertex()
# vtx_name = 'Box001Shape.vtx[461]'
# check_vtx(vtx_name, True)
# count_skeleton()