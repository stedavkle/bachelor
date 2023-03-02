import glob
from PIL import Image                                      # (pip install Pillow)
import numpy as np                                         # (pip install numpy)
from skimage import measure                                # (pip install scikit-image)
from shapely.geometry import Polygon, MultiPolygon         # (pip install Shapely)
import os
import json

# Label ids of the dataset
category_ids = {
    "background": 0,
    "tip": 1
}
# Define which colors match which categories in the images
category_colors = {
    "(0, 0, 0)": 0, # background,
    "(255, 0, 0)": 1, # tip
    "(255, 255, 0)": 1, # tip
    "(128, 0, 255)": 1, # tip
    "(255, 128, 0)": 1, # tip
    "(0, 0, 255)": 1, # tip
    "(128, 255, 255)": 1, # tip
    "(0, 255, 0)": 1, # tip
    "(128, 128, 128)": 1 # tip
}
background_color = (0, 0, 0)


def create_rle(mask_image, width, height):
    min_max = {}
    rle_objects = {}
    pixel_count = 1
    current_rle = 0
    previous_pixel = str(mask_image.getpixel((1,1))[:3])
    min_max[previous_pixel] = [(0, 0), (0, 0)]
    # get first pixel and set the rle to 0
    print('start loop')
    for x in range(width):
        for y in range(height):
            # Get the RGB values of the pixel
            pixel = mask_image.getpixel((x,y))[:3]
            pixel_str = str(pixel)
            if not pixel_str in min_max.keys():
                min_max[pixel_str] = [(x, y), (x, y)]
            else:
                if y <= min_max[pixel_str][0][1] and x > min_max[pixel_str][0][0]:
                    min_max[pixel_str][0] = (x, y)
                if x <= min_max[pixel_str][1][0] and y > min_max[pixel_str][1][1]:
                    min_max[pixel_str][1] = (x, y)
            if pixel_str == previous_pixel:
                current_rle += 1
            else:
                if previous_pixel in rle_objects.keys():
                    #rle_objects[previous_pixel].append(current_rle)
                    for key in rle.objects.keys():
                        rle_objects[key].append(current_rle)
                else:
                    rle_objects[previous_pixel] = [pixel_count, current_rle]
                
                current_rle = 1
                previous_pixel = pixel_str
            pixel_count += 1
    return rle_objects, min_max

rle_objects, min_max = create_rle(image_open, w, h)
min_max

def create_annotation_format(polygon, segmentation, image_id, category_id, annotation_id):
    min_x, min_y, max_x, max_y = polygon.bounds
    width = max_x - min_x
    height = max_y - min_y
    bbox = (min_x, min_y, width, height)
    area = polygon.area

    annotation = {
        "segmentation": segmentation,
        "area": area,
        "iscrowd": 0,
        "image_id": image_id,
        "bbox": bbox,
        "category_id": category_id,
        "id": annotation_id
    }

    return annotation

def get_coco_json_format():
    # Standard COCO format 
    coco_format = {
        "info": {},
        "licenses": [],
        "images": [{}],
        "categories": [{}],
        "annotations": [{}]
    }
    return coco_format
def create_image_annotation(file_name, width, height, image_id):
    images = {
        "file_name": file_name,
        "height": height,
        "width": width,
        "id": image_id
    }
    return images



# Get "images" and "annotations" info 
def images_annotations_info(maskpath):
    # This id will be automatically increased as we go
    annotation_id = 0
    image_id = 0
    annotations = []
    images = []
    
    for mask_image in glob.glob(maskpath + "*.tif"):
        # We make a reference to the original file in the COCO JSON file
        original_file_name = os.path.basename(mask_image).split(".")[0].split("_")[0] + ".tif"

        # Open the image and (to be sure) we convert it to RGB
        mask_image_open = Image.open(mask_image).convert("RGB")
        w, h = mask_image_open.size
        
        # "images" info 
        image = create_image_annotation(original_file_name, w, h, image_id)
        images.append(image)

        rle_objects = create_rle(mask_image_open, w, h)

        for color, rle in rle_objects.items():
            if color != str(background_color):
                # Get the category id from the color
                category_id = category_colors[color]

                # Get the segmentation info
                segmentation = [rle]

                # "annotations" info
                annotation = create_annotation_format(polygon, segmentation, image_id, category_id, annotation_id)
                annotations.append(annotation)
                annotation_id += 1


        image_id += 1
    return images, annotations, annotation_id


if __name__ == __main__:
    # coco_format = get_coco_json_format()
    # root = r"D:\datasets"
    # dataset = r"\test"

    # for keyword in ["train", "val"]:
    #     mask_path = root + dataset + "/{}_mask/".format(keyword)
    #     # Create category section
    #     coco_format["categories"] = create_category_annotation(category_ids)

    #     # Create images and annotations sections
    #     coco_format["images"], coco_format["annotations"], annotation_cnt = images_annotations_info(mask_path)

    image_open = Image.open(r"C:\Users\david\Desktop\rle_test.png").convert("RGB")
    w, h = image_open.size
    rle_objects, min_max = create_rle(image_open, w, h)