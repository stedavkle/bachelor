import os
import json
import numpy as np

category_ids = {
    "background": 0,
    "tip": 1,
    "tip2": 2,
    "tip3": 3,
    "tip4": 4,
    "tip5": 5,
    "tip6": 6,
    "tip7": 7,
    "tip8": 8
}

# Define which colors match which categories in the images
category_colors = {
    "(0, 0, 0)": 0, # background,
    "(255, 0, 0)": 1, # tip1
    "(255, 255, 0)": 2, # tip2
    "(128, 0, 255)": 3, # tip3
    "(255, 128, 0)": 4, # tip4
    "(0, 0, 255)": 5, # tip5
    "(128, 255, 255)": 6, # tip6
    "(0, 255, 0)": 7, # tip7
    "(128, 128, 128)": 8 # tip8
}
category_colors_inv = {v: k for k, v in category_colors.items()}

def get_coco_json_format():
    # Standard COCO format 
    coco_format = {
        "images": [{}],
        "categories": [{}],
        "annotations": [{}]
    }
    return coco_format
def create_category_annotation_panoptic(category_dict):
    category_list = []

    for key, value in category_dict.items():
        category = {
            "supercategory": key,
            "id": value,
            "isthing": int(value > 0),
            "name": key,
            "color": list(map(int, category_colors_inv[category_ids[key]][1:-1].split(", ")))
        }
        category_list.append(category)

    return category_list
def create_image_annotation(file_name, width, height, image_id):
    images = {
        "file_name": file_name,
        "height": height,
        "width": width,
        "id": image_id
    }
    return images
def create_segment_format(polygon, category_id, segment_id):
    min_x, min_y, max_x, max_y = polygon.bounds
    width = max_x - min_x
    height = max_y - min_y
    bbox = (min_x, min_y, width, height)
    area = polygon.area\

    segment = {
        "id": segment_id,
        "category_id": category_id,
        "iscrowd": 0,
        "bbox": bbox,
        "area": area
    }
    return segment