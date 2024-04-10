import fbx

def print_skeleton_hierarchy(node, indent=0):
    """
    递归函数，用于打印骨骼节点的层级结构。
    """
    nodeAttributeType = node.GetNodeAttribute().GetAttributeType() if node.GetNodeAttribute() else None
    
    if nodeAttributeType == fbx.FbxNodeAttribute.eSkeleton:
        name = node.GetName()
        print("  " * indent + name)

    for i in range(node.GetChildCount()):
        print_skeleton_hierarchy(node.GetChild(i), indent + 1)

def load_fbx_and_print_skeleton(fbx_file_path):
    """
    加载FBX文件并打印骨骼信息。
    """
    # 创建FBX管理器
    manager = fbx.FbxManager.Create()
    
    # 创建一个导入器
    importer = fbx.FbxImporter.Create(manager, "")
    
    # 使用导入器加载FBX文件
    status = importer.Initialize(fbx_file_path, -1, manager.GetIOSettings())
    if not status:
        raise Exception("FBX file could not be loaded.")
    
    # 创建一个场景
    scene = fbx.FbxScene.Create(manager, "Scene")
    
    # 导入内容到场景
    importer.Import(scene)
    importer.Destroy()
    
    # 获取场景的根节点并打印骨骼信息
    root_node = scene.GetRootNode()
    if root_node:
        print("FBX骨骼层级结构:")
        print_skeleton_hierarchy(root_node)

# 替换为你的FBX文件路径
fbx_file_path = 'E:/Animation Data/batch_pass_ball_fbx/tupofankui_beihuangdao_you.fbx'
load_fbx_and_print_skeleton(fbx_file_path)
