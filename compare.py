import os
import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim
from render_animation import camera_list

def read_frames(image_folder):
    if not image_folder.endswith('/'):
        image_folder += '/'
    
    image_list = []
    for f in os.listdir(image_folder):
        image_file = os.path.join(image_folder, f)
        if os.path.isfile(image_file):
            image = cv2.imread(image_file, cv2.IMREAD_GRAYSCALE)
            if image is None:
                print(f"警告：无法加载图像 {image_file}，跳过此文件。")
                continue
            image_list.append(image)
        else:
            raise ValueError("图像未加载，检查路径是否正确")
    
    return image_list


def calculate_frame_difference(frame_A, frame_B):
    similarity = ssim(frame_A, frame_B)
    difference = 1 - similarity
    return difference


def calculate_edge_difference(frame_A, frame_B):
    edge1 = cv2.Canny(frame_A, 50, 150)
    edge2 = cv2.Canny(frame_B, 50, 150)
    
    difference = np.mean((edge1-edge2)**2)
    return difference


def calculate_anim_difference(camera_name, lod_level):
    src_path = "E:/Procedural Skeleton/images/Experiment/" + camera_name + "_LOD" + str(lod_level)
    des_path = "E:/Procedural Skeleton/images/Original/" + camera_name + "_LOD" + str(lod_level)
    animation_A = read_frames(src_path)
    animation_B = read_frames(des_path)
    frame_differences = []

    for frame_A, frame_B in zip(animation_A, animation_B):
        difference = calculate_frame_difference(frame_A, frame_B)
        frame_differences.append(difference)

    average_difference = sum(frame_differences) / len(frame_differences)
    quality_difference = 1 - average_difference
    # print(f"----In {camera_name}'s perspective, the quality_difference is {quality_difference}.")
    return quality_difference


def calculate_quality_difference(lod_level):
    sum = 0
    for camera in camera_list:
        sum += calculate_anim_difference(camera, lod_level)
        
    return sum / len(camera_list)