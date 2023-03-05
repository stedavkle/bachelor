"""
Credits: chrise96

The code from this file is based on the following repository:
https://github.com/chrise96/image-to-coco-json-converter

The code is modified to fit the needs of this project.
"""

#%%
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
    "tip": 1,
    # "tip2": 2,
    # "tip3": 3,
    # "tip4": 4,
    # "tip5": 5,
    # "tip6": 6,
    # "tip7": 7,
    # "tip8": 8
}

# Define which colors match which categories in the images
category_colors = {
    "(0, 0, 0)": 0, # background,
    "(255, 0, 0)": 1, # tip1
    "(255, 255, 0)": 1, # tip2
    "(128, 0, 255)": 1, # tip3
    "(255, 128, 0)": 1, # tip4
    "(0, 0, 255)": 1, # tip5
    "(128, 255, 255)": 1, # tip6
    "(0, 255, 0)": 1, # tip7
    "(128, 128, 128)": 1 # tip8
}

# Define the ids that are a multiplolygon. In our case: wall, roof and sky
multipolygon_ids = [0, 1]#, 2, 3, 4, 5, 6, 7, 8]


def create_sub_masks(mask_image, width, height):
    # Initialize a dictionary of sub-masks indexed by RGB colors
    sub_masks = {}
    for x in range(width):
        for y in range(height):
            # Get the RGB values of the pixel
            pixel = mask_image.getpixel((x,y))[:3]

            # Check to see if we have created a sub-mask...
            pixel_str = str(pixel)
            if IGNORE_BACKGROUND and pixel_str == "(0, 0, 0)":
                continue

            sub_mask = sub_masks.get(pixel_str)
            if sub_mask is None:
               # Create a sub-mask (one bit per pixel) and add to the dictionary
                # Note: we add 1 pixel of padding in each direction
                # because the contours module doesn"t handle cases
                # where pixels bleed to the edge of the image
                sub_masks[pixel_str] = Image.new("1", (width+2, height+2))

            # Set the pixel value to 1 (default is 0), accounting for padding
            sub_masks[pixel_str].putpixel((x+1, y+1), 1)

    return sub_masks

def create_sub_mask_annotation(sub_mask):
    # Find contours (boundary lines) around each sub-mask
    # Note: there could be multiple contours if the object
    # is partially occluded. (E.g. an elephant behind a tree)
    contours = measure.find_contours(np.array(sub_mask), 0.5, positive_orientation="low")

    polygons = []
    segmentations = []
    for contour in contours:
        # Flip from (row, col) representation to (x, y)
        # and subtract the padding pixel
        for i in range(len(contour)):
            row, col = contour[i]
            contour[i] = (col - 1, row - 1)

        # Make a polygon and simplify it
        poly = Polygon(contour)
        poly = poly.simplify(1.0, preserve_topology=False)
        
        if(poly.is_empty):
            # Go to next iteration, dont save empty values in list
            continue

        polygons.append(poly)

        segmentation = np.array(poly.exterior.coords).ravel().tolist()
        segmentations.append(segmentation)
    
    return polygons, segmentations

def create_category_annotation(category_dict):
    category_list = []

    for key, value in category_dict.items():
        category = {
            "supercategory": key,
            "id": value,
            "name": key
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

# Get "images" and "annotations" info 
def images_annotations_info(maskpath):
    # This id will be automatically increased as we go
    annotation_id = 0
    image_id = 0
    annotations = []
    images = []
    
    for mask_image in glob.glob(maskpath + "*.tif"):
        # We make a reference to the original file in the COCO JSON file
        original_file_name = os.path.basename(mask_image)

        # Open the image and (to be sure) we convert it to RGB
        mask_image_open = Image.open(mask_image).convert("RGB")
        w, h = mask_image_open.size
        
        # "images" info 
        image = create_image_annotation(original_file_name, w, h, image_id)
        images.append(image)

        sub_masks = create_sub_masks(mask_image_open, w, h)
        for color, sub_mask in sub_masks.items():
            try:
                category_id = category_colors[color]
            except Exception as e:
                print(original_file_name, e, mask_image_open.mode)
                # print the distribution of colors in the image
                #print(mask_image_open.getcolors())
                break


            # "annotations" info
            polygons, segmentations = create_sub_mask_annotation(sub_mask)

            # Check if we have classes that are a multipolygon
            if category_id in multipolygon_ids:
                # Combine the polygons to calculate the bounding box and area
                multi_poly = MultiPolygon(polygons)
                                
                annotation = create_annotation_format(multi_poly, segmentations, image_id, category_id, annotation_id)

                annotations.append(annotation)
                annotation_id += 1
            else:
                for i in range(len(polygons)):
                    # Cleaner to recalculate this variable
                    segmentation = [np.array(polygons[i].exterior.coords).ravel().tolist()]
                    
                    annotation = create_annotation_format(polygons[i], segmentation, image_id, category_id, annotation_id)
                    
                    annotations.append(annotation)
                    annotation_id += 1
        image_id += 1
    return images, annotations, annotation_id
#%%
if __name__ == "__main__":
    # Get the standard COCO JSON format
    coco_format = get_coco_json_format()
    root = r"D:\datasets"
    dataset = r"\test3"
    
    IGNORE_BACKGROUND = True
    background_color = "(0, 0, 0)"
    if IGNORE_BACKGROUND:
        category_ids.pop("background")
        category_colors.pop(background_color)
        multipolygon_ids.remove(0)

    for keyword in ["train", "val"]:
        mask_path = root + dataset + "/{}_mask/".format(keyword)
        
        # Create category section
        coco_format["categories"] = create_category_annotation(category_ids)
    
        # Create images and annotations sections
        coco_format["images"], coco_format["annotations"], annotation_cnt = images_annotations_info(mask_path)

        with open(root + dataset + "/annotation/{}.json".format(keyword),"w") as outfile:
            json.dump(coco_format, outfile)
        
        print("Created %d annotations for images in folder: %s" % (annotation_cnt, mask_path))


#%%
def check_img(img_path):
    img = Image.open(img_path)
    print(img.getcolors())

def correct_mask(mask_folder):
    for root, dirs, files in os.walk(mask_folder):
        for file in files:
            if file.endswith(".tif"):
                print(os.path.join(root, file))
                img = Image.open(os.path.join(root, file))
                pixels = img.load()
                for x in range(img.width):
                    for y in range(img.height):
                        r, g, b = pixels[x, y]

                        # Modify the red channel
                        if r < 120:
                            r = 0
                        elif r >= 120 and r <= 135:
                            r = 128
                        else:
                            r = 255

                        # Modify the green channel
                        if g < 120:
                            g = 0
                        elif g >= 120 and g <= 135:
                            g = 128
                        else:
                            g = 255

                        # Modify the blue channel
                        if b < 120:
                            b = 0
                        elif b >= 120 and b <= 135:
                            b = 128
                        else:
                            b = 255

                        # Update the pixel with the modified color channels
                        pixels[x, y] = (r, g, b)
                img.save(os.path.join(root, file))
#%%
def correct_color(img_path):
    img = Image.open(img_path)
    pixels = img.load()
    for x in range(img.width):
        for y in range(img.height):
            if pixels[x, y] == (0, 0, 128):
                pixels[x, y] = (0, 0, 255)
    img.save(img_path)

# %%
