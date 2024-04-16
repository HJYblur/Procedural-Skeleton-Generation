import pymel.core as pm
import os
import shutil
import csv
from PIL import ImageGrab
camera_list = ["front_custom1", "back_custom1", "top_custom1", "bottom_custom1", "right_custom1", "left_custom1"]

def move_pics(src, dst, delete_flag = False):
    if not os.path.exists(src):
        pm.error(f"No file in {src}!")
        
    if not os.path.exists(dst):
        os.mkdir(dst)
    
    filelist = os.listdir(src)
    
    for file in filelist:
        src_file = os.path.join(src, file)
        dst_file = os.path.join(dst, file)
        shutil.move(src_file, dst_file)
    
    if delete_flag: 
        os.rmdir(src)
        # print(f"--------Successfully move all the files in {src} to {dst}.")
    # else:
        # print(f"--------Successfully copy all the files in {src} to {dst}.")


def create_camera(camera_name, lod_level):
    
    if not pm.objExists(camera_name):
        camera_transform, camera_shape = pm.camera(name=camera_name)
        print("----Create Camera: " + camera_name)
    else:
        camera_transform = pm.PyNode(camera_name)
        camera_shape = camera_transform.getShape()
        # print("----Get Camera: " + camera_name)
        
    translate = [0, 0, 0]
    rotate = [0, 0, 0]
    
    with open("E:/Procedural Skeleton/Camera Attr/cameras.csv", "r") as file:
        reader = csv.reader(file)
        next(reader)
        for row in reader:
            if int(row[0])==lod_level and row[1]==camera_name:
                translate = [float(value) for value in row[2:5]]
                rotate = [float(value) for value in row[5:8]]
    
    camera_transform.translate.set(translate)
    camera_transform.rotate.set(rotate)

    camera_shape = camera_transform.getShape()
    
    camera_shape.focalLength.set(35.0)
    camera_shape.horizontalFilmAperture.set(1.417)
    camera_shape.verticalFilmAperture.set(0.945)

    camera_shape.nearClipPlane.set(0.1)
    camera_shape.farClipPlane.set(1000.0)
    
    return camera_shape

def create_camera_list(lod_level):
    for camera_name in camera_list:
        create_camera(camera_name, lod_level)


def adjust_camera(camera_name, lod_level):
    if pm.objExists(camera_name):
        camera_transform = pm.PyNode(camera_name)
        camera_shape = camera_transform.getShape()
    else:
        raise ValueError("Couldn't find the camera {camera_name}.")
    
    with open("E:/Procedural Skeleton/Camera Attr/cameras.csv", "r") as file:
        reader = csv.reader(file)
        next(reader)
        for row in reader:
            if int(row[0])==lod_level and row[1]==camera_name:
                translate = [float(value) for value in row[2:5]]
                rotate = [float(value) for value in row[5:8]]
    
    camera_transform.translate.set(translate)
    camera_transform.rotate.set(rotate)
    return camera_shape


def render_setting():
    start_time = int(pm.playbackOptions(query=True, minTime=True))
    end_time = int(pm.playbackOptions(query=True, maxTime=True))
    # print(f"start_time: {start_time}, end_time: {end_time}") 
    pm.setAttr('defaultRenderGlobals.startFrame', start_time)
    pm.setAttr('defaultRenderGlobals.endFrame', end_time)
    
    pm.setAttr('defaultRenderGlobals.currentRenderer', 'mayaSoftware')

    # 设置输出图片格式，32表示png
    pm.setAttr('defaultRenderGlobals.imageFormat', 32)

    # 设置渲染输出的分辨率
    pm.setAttr('defaultResolution.width', 1920)
    pm.setAttr('defaultResolution.height', 1080)

    pm.setAttr('defaultRenderGlobals.imageFilePrefix', 'frame', type='string') # 设置输出路径
    pm.setAttr('defaultRenderGlobals.animation', 1)  # 开启动画渲染 (多帧)
    pm.setAttr('defaultRenderGlobals.periodInExt', 2)  # 使用下划线分隔扩展名和帧编号
    pm.setAttr('defaultRenderGlobals.putFrameBeforeExt', 1) # 启用帧编号在扩展名之前
    pm.setAttr('defaultRenderGlobals.extensionPadding', 4)  # 帧编号的位数
    
    return start_time, end_time


def render_frames(camera_name, lod_level, start_time, end_time, step, des_folder, move_flag=True):
    camera_shape = create_camera(camera_name, lod_level)

    for frame in range(start_time, end_time+1, step):
        pm.currentTime(frame)  # 设置当前帧
        pm.setAttr(camera_shape.renderable, True)  # 确保相机是可渲染的
        pm.render(camera_shape, x=512, y=512)  # 渲染当前帧

    # print(f"----Render {end_time-start_time} frames of camera {camera_name} in LOD {lod_level}")
    
    if move_flag:
        src_path = "C:/Users/hejiayi03/Documents/maya/projects/default/images/tmp/" + camera_name
        des_path = "E:/Procedural Skeleton/images/" + des_folder + "/" + camera_name + "_LOD" + str(lod_level)
        move_pics(src_path, des_path, True)


def render_anim(LOD_level, des_folder, move_flag=True):
    start_time, end_time = render_setting()
    for camera in camera_list:
        render_frames(camera, LOD_level, start_time, end_time, step, des_folder, move_flag)
    
        
        
def screen_shot(start_time, end_time, step, des_path):
    for frame in range(start_time, end_time+1, step):
        pm.currentTime(frame)
        
        img = ImageGrab.grab(bbox =(730, 300, 1242, 812))
        img.save(f"{des_path}/frame_{frame:03d}.png")
        

def get_screenshot(LOD_level, des_folder):
    start_time = int(pm.playbackOptions(query=True, minTime=True))
    end_time = int(pm.playbackOptions(query=True, maxTime=True))
    step = 5
    for camera_name in camera_list:
        cur_camera = adjust_camera(camera_name, LOD_level)
        pm.lookThru(cur_camera)
        
        des_path = "E:/Procedural Skeleton/images/" + des_folder + "/" + camera_name + "_LOD" + str(LOD_level)
        if not os.path.exists(des_path):
            os.mkdir(des_path)
            
        screen_shot(start_time, end_time, step, des_path)
     