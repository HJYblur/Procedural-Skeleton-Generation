import pymel.core as pm

LOD_dic = {"LOD0": 100.0, "LOD1": 50.0, "LOD2": 33.3, "LOD3": 15.0}
selected_joints = []


def get_all_joints():
    return pm.ls(type='joint')


def on_input_joint(*args):
    global selected_joints
    input_text = pm.textField(joint_input, query=True, text=True)
    selected_joints.append(input_text)
    print(f"AAAAAAAAAAAAAAAAAA{selected_joints}")
    # all_joints = get_all_joints()
    # matching_joints = [joint for joint in all_joints if joint.name() == input_text]
    # if matching_joints:
    #     pm.textScrollList(joint_list, edit=True, selectItem=input_text)


def delete_weights_skeleton(*args):
    print(f"Selected {selected_joints}")
    removed_weights_info = []  # To store information about removed weights

    # Iterate over all mesh objects in the scene
    for mesh in pm.ls(geometry=True):
        # Find the skinCluster attached to the mesh
        skinClusters = pm.listHistory(mesh, type="skinCluster")
        if not skinClusters:
            continue

        skinCluster = skinClusters[0]

        # Get all influences for the skinCluster
        influences = pm.skinCluster(skinCluster, query=True, influence=True)

        influences_to_remove = [
            inf for inf in influences if inf.name() in selected_joints
        ]
        if not influences_to_remove:
            print(f"Warning: No weight for {skinCluster}")
            continue

        for vtx in mesh.vtx:
            # Check if the vertex is influenced by any joint to be removed
            weights = pm.skinPercent(skinCluster, vtx, query=True, value=True)
            influenceIndices = pm.skinPercent(
                skinCluster, vtx, query=True, transform=None
            )

            for inf, weight, idx in zip(influences, weights, influenceIndices):
                if inf in influences_to_remove and weight > 0:
                    pm.skinPercent(
                        skinCluster,
                        vtx,
                        transformValue=[(inf.name(), 0)],
                        normalize=True,
                    )
                    removed_weights_info.append(
                        (vtx.name(), [inf.name() for inf in influences_to_remove])
                    )
    for vtx_name, joints in removed_weights_info:
        info_str = f"Removed weights from {vtx_name} for joints: {', '.join(joints)}"
        print(info_str)


def generate_combined_mesh_LOD(*args):
    lod_levels = pm.radioButtonGrp(lod_radio_group, query=True, select=True)
    print(f"Function to generate LOD {lod_levels} would be executed here.")

    all_meshes = pm.ls(
        type="mesh", ni=True, visible=True
    )  # 筛选非中间对象(non-intermediate)和可见的网格
    transform_nodes = [mesh.getParent() for mesh in all_meshes if mesh.isVisible()]

    if len(transform_nodes) < 2:
        combined_mesh = all_meshes
    else:
        combined_mesh, _ = pm.polyUnite(
            transform_nodes, ch=True, mergeUVSets=True, name="combined_mesh"
        )

    # 保证合并的网格有一个skinCluster
    skins = pm.listHistory(combined_mesh, type="skinCluster")
    if not skins:
        pm.error(
            "No skinCluster found on combined mesh. Ensure the original meshes were skinned."
        )
        return

    # 生成LOD
    for i in range(1, lod_levels + 1):
        # inputConnections保证权重也能复制到
        lod_model = pm.duplicate(
            combined_mesh, name=f"{combined_mesh}_LOD{i}", inputConnections=True
        )[0]

        reduction_percentage = LOD_dic["LOD" + str(i)]

        pm.polyReduce(
            lod_model,
            percentage = 100.0 - reduction_percentage,
            keepQuadsWeight=1,
            version=1,
        )

        lod_skins = pm.listHistory(lod_model, type="skinCluster")
        if skins:
            pm.copySkinWeights(
                ss=skins[0],
                ds=lod_skins[0],
                surfaceAssociation="closestPoint",
                influenceAssociation=["name", "closestJoint"],
            )

        print(f"LOD{i} generated.")


def export_selected_mesh(*args):
    selected_mesh = pm.radioButtonGrp(mesh_radio_group, query=True, select=True)
    print(f"Function to export mesh {selected_mesh} would be executed here.")


# 界面
def create_custom_window():
    window_name = "LOD_Animation"
    if pm.window(window_name, exists=True):
        pm.deleteUI(window_name)

    pm.window(
        window_name,
        title="骨骼LOD动画生成",
        widthHeight=(300, 150),
        sizeable=True,
    )
    
    main_layout = pm.columnLayout(adjustableColumn=True)

    # 创建条目 - 选择要删除的骨骼
    pm.rowLayout(
        numberOfColumns=3,
        columnWidth3=(100, 50, 50),
        adjustableColumn=2,
        columnAlign=(1, "right"),
    )
    pm.text(label="选择或者输入要删除的骨骼:")
    
    global joint_input
    joint_input = pm.textField(width=250, enterCommand=on_input_joint)
    # global joint_list
    # joint_list = pm.textScrollList(height=30, allowMultiSelection=True, selectCommand=on_joint_select)
    
    # # 填充滚动列表项
    # for joint in get_all_joints():
    #     pm.textScrollList(joint_list, edit=True, append=joint.name())
    
    pm.button(label="执行", command=delete_weights_skeleton)
    pm.setParent("..")

    # 创建条目 - 生成LOD的层级
    pm.rowLayout(
        numberOfColumns=3,
        columnWidth3=(100, 50, 50),
        adjustableColumn=2,
        columnAlign=(1, "right"),
    )
    pm.text(label="生成LOD的层级:")
    global lod_radio_group
    lod_radio_group = pm.radioButtonGrp(
        labelArray3=["1", "2", "3"], numberOfRadioButtons=3, select=1
    )
    pm.button(label="执行", command=generate_combined_mesh_LOD)
    pm.setParent("..")

    # 创建条目 - 选择要导出的网格
    pm.rowLayout(
        numberOfColumns=3,
        columnWidth3=(100, 50, 50),
        adjustableColumn=2,
        columnAlign=(1, "right"),
    )
    pm.text(label="选择要导出的网格:")
    global mesh_radio_group
    mesh_radio_group = pm.radioButtonGrp(
        labelArray3=["网格1", "网格2", "网格3"], numberOfRadioButtons=3, select=1
    )
    pm.button(label="执行", command=export_selected_mesh)
    pm.setParent("..")

    pm.showWindow(window_name)


# 调用界面设计函数创建窗口
create_custom_window()
