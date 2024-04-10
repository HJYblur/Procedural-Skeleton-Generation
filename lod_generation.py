import pymel.core as pm

LOD_dic = {"LOD0": 100.0, "LOD1": 50.0, "LOD2": 33.3, "LOD3": 15.0}


def generate_combined_mesh_LODs(lod_levels):

    combined_mesh_transform = pm.ls('combined_mesh', type='transform')
    if combined_mesh_transform:
        combined_mesh = combined_mesh_transform[0]
    else:
        all_meshes = pm.ls(type="mesh", ni=True, visible=True) 
        transform_nodes = [mesh.getParent() for mesh in all_meshes if mesh.isVisible()]
        duplicated_nodes = [pm.duplicate(node, name=f"{node}_duplicate", inputConnections=True)[0] for node in transform_nodes]

        # 合并复制后的网格
        combined_mesh, _ = pm.polyUnite(duplicated_nodes, ch=True, mergeUVSets=True, name="combined_mesh")
    # print("Original combined mesh number: "+ str(pm.polyEvaluate(combined_mesh, face=True)))

    # 保证合并的网格有一个skinCluster
    skins = pm.listHistory(combined_mesh, type="skinCluster")
    if not skins:
        pm.error(
            "No skinCluster found on combined mesh. Ensure the original meshes were skinned."
        )
        return
    # print(skins)

    # 生成LOD
    for i in range(1, lod_levels + 1):
        # inputConnections保证权重也能复制到
        lod_model = pm.duplicate(
            combined_mesh, name=f"{combined_mesh}_LOD{i}", inputConnections=True
        )[0]

        reduction_percentage = 100.0 - LOD_dic["LOD" + str(i)]
        # print(reduction_percentage)

        pm.polyReduce(
            lod_model,
            version=1,
            percentage=reduction_percentage,
            keepQuadsWeight=1
        )

        lod_skins = pm.listHistory(lod_model, type="skinCluster")
        if skins:
            pm.copySkinWeights(
                ss=skins[0],
                ds=lod_skins[0],
                surfaceAssociation="closestPoint", # 均会穿模
                influenceAssociation=["name", "closestJoint"],
            )

        print(f"LOD{i} generated: ", end="")
        print(pm.polyEvaluate(lod_model, face=True))
        


def generate_combined_mesh_LOD(lod_level):

    combined_mesh_transform = pm.ls('combined_mesh', type='transform')
    if combined_mesh_transform:
        combined_mesh = combined_mesh_transform[0]
    else:
        all_meshes = pm.ls(type="mesh", ni=True, visible=True) 
        transform_nodes = [mesh.getParent() for mesh in all_meshes if mesh.isVisible()]
        duplicated_nodes = [pm.duplicate(node, name=f"{node}_duplicate", inputConnections=True)[0] for node in transform_nodes]

        # 合并复制后的网格
        combined_mesh, _ = pm.polyUnite(duplicated_nodes, ch=True, mergeUVSets=True, name="combined_mesh")
    # print("Original combined mesh number: "+ str(pm.polyEvaluate(combined_mesh, face=True)))

    # 保证合并的网格有一个skinCluster
    skins = pm.listHistory(combined_mesh, type="skinCluster")
    if not skins:
        pm.error(
            "No skinCluster found on combined mesh. Ensure the original meshes were skinned."
        )
        return
    
    lod_model = pm.duplicate(
        combined_mesh, name=f"{combined_mesh}_LOD{lod_level}", inputConnections=True
    )[0]

    reduction_percentage = 100.0 - LOD_dic["LOD" + str(lod_level)]
    # print(reduction_percentage)

    pm.polyReduce(
        lod_model,
        version=1,
        percentage=reduction_percentage,
        keepQuadsWeight=1
    )

    lod_skins = pm.listHistory(lod_model, type="skinCluster")
    if skins:
        pm.copySkinWeights(
            ss=skins[0],
            ds=lod_skins[0],
            surfaceAssociation="closestPoint", # 均会穿模
            influenceAssociation=["name", "closestJoint"],
        )

    # print(f"LOD{lod_level} generated: ", end="")
    # print(pm.polyEvaluate(lod_model, face=True))



def hide_LOD(remain_LOD_level, total_LOD_level):
    mesh_names = ["combined_mesh", "combined_mesh_LOD1", "combined_mesh_LOD2", "combined_mesh_LOD3"]
    mesh_list = mesh_names[0:total_LOD_level+1]
    # print(mesh_list)
    for i, mesh in enumerate(mesh_list):
        node = pm.PyNode(mesh)
        if i == remain_LOD_level: 
            node.visibility.set(True)
        else:
            node.visibility.set(False)

# generate_combined_mesh_LOD(2)