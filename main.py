import sys
sys.path.append("E:\Procedural Skeleton")
import pymel as pm
import sys
import maya.cmds as cmds
from importlib import reload
from skeleton_tree import construct_tree, extract_all_joint_data
from lod_generation import generate_combined_mesh_LOD, generate_combined_mesh_LODs, hide_LOD
from delete_lod import delete_duplicate, batch_delete_lod
from render_animation import render_anim, get_screenshot, create_camera_list
from delete_joint_weight import refine_weights, restore_weights
from compare import calculate_quality_difference
# import delete_joint_weight
# import compare
# reload(compare)
# reload(delete_joint_weight)


def set_display():
    model_editors = cmds.getPanel(type='modelPanel')
    for editor in model_editors:
        # 直接尝试对每个模型编辑器应用设置
        try:
            cmds.modelEditor(editor, edit=True, allObjects=False)
            cmds.modelEditor(editor, edit=True, polymeshes=True)
        except Exception as e:
            cmds.warning(f"An error occurred with {editor}: {e}")


def get_animation(type):
    generate_combined_mesh_LOD(LOD_level)
    delete_duplicate()
    hide_LOD(LOD_level, LOD_level)
    get_screenshot(LOD_level, type)


def greedy_algorithm():
    ratio_dic = {}
    
    for joint in joint_node_list:
        if joint.stable: continue
        joint_name = joint.name
        tmp_list = selected_list
        
        if not joint.deleted:
            tmp_list.append(joint_name)
            weights_backup = refine_weights(tmp_list)
            
            get_animation("Experiment")
            
            joint.loss = calculate_quality_difference(LOD_level)
            if joint.loss < Low_Threshold:
                print(f"----If delete {joint_name}, the loss would surpass the threshold.")
                restore_weights(weights_backup)
                continue
            
            ratio_dic[joint_name] = joint.weight / joint.loss
            print(f"----{joint_name}     weight: {joint.weight}), loss:{joint.loss}, ratio: {ratio_dic[joint_name]}.")
            restore_weights(weights_backup)
            batch_delete_lod()
              
    if not ratio_dic: return ""
    
    sorted_dic = {k:ratio_dic[k] for k in sorted(ratio_dic, key = ratio_dic.get, reverse=True)} # 降序排列
    target_joint_name = next(iter(sorted_dic))
    
    selected_list.append(target_joint_name)
    target_joint = next((item for item in joint_node_list if item.name == target_joint_name), None)
    target_joint.deleted = True if target_joint else None
    return target_joint_name


if __name__ == "__main__":
    LOD_level = 1
    Epoch = 1
    Low_Threshold = 0.995
    High_Threshold = 0.9999
    selected_list = []
    opt_step = 1
    set_display() # 确认截图设置
     
    # 建骨骼树
    root_node, joint_node_list = construct_tree()
    if joint_node_list: print("\nStep1: Construct Skeleton Tree Done.\n")
    else: pm.error("Step1 Failed! Coundn't construct skeleton tree.")
    
    # 生成原始LOD
    generate_combined_mesh_LODs(LOD_level)
    delete_duplicate()
    create_camera_list(LOD_level)
    for i in range(0, LOD_level+1):
        hide_LOD(i, LOD_level)
        get_screenshot(i, "Original")
    batch_delete_lod()
    print("\nStep2: Initial LOD generation Done.\n")
        
    # 初步优化：通过骨骼间层级关系进行删减
    extract_all_joint_data(root_node)    
    ratio_dic = {}
    delete_cnt = 0
    for joint in joint_node_list:
        joint_name = joint.name
        if joint.stable: continue
        if joint.deleted: 
            delete_cnt += 1
            print(f"----{joint_name} has been appended to the list.")
            selected_list.append(joint_name)
    print(f"\nStep3: Delete {delete_cnt} joints, counting for {delete_cnt/len(joint_node_list):.2%} of all joints. \n")
        
    # 进一步优化，通过删除单根骨骼比较动画质量，再通过贪心算法确定删除的骨骼
    if opt_step==2:
        for i in range(Epoch):
            print(f"====================Epoch {i}================================")
            cur_joint = greedy_algorithm()
            print(f"In Epoch {i}, the deleted joint is {cur_joint}")
        print(f"Step4: Delete {Epoch} joints in total.")
    
    # 得到最终的动画
    get_animation("SOTA")
    batch_delete_lod()
    print(f"\nStep5: Generate SOTA animation done.")