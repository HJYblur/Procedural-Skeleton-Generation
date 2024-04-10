import pymel.core as pm

def delete_duplicate():
    transform_nodes = pm.ls("*_duplicate", type="transform")
    lens = len(transform_nodes)
    for tran in transform_nodes:
        pm.delete(tran)
    # print(f"----{lens} duplicate nodes have been deleted")


def delete_lod(node_name):
    delete_duplicate()
    
    target_mesh = pm.ls(node_name, type="transform")
    if target_mesh:
        pm.delete(target_mesh)
    # else:
    #     pm.error(f"No {node_name} existed.")
         
            
def batch_delete_lod():
    delete_duplicate()
    
    mesh_names = ["combined_mesh", "combined_mesh_LOD1", "combined_mesh_LOD2", "combined_mesh_LOD3"]
    for name in mesh_names:
        target_mesh = pm.ls(name, type="transform")
        if target_mesh:
            pm.delete(target_mesh)
        # else:
        #     print(f"No {name} existed.")
        #     continue