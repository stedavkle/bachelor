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
import shutil

# Label ids of the dataset
category_ids = {
    "background": 0,
    "tip": 1
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
        segmentation = normalize_segmentaion(np.array(poly.exterior.coords).ravel(), sub_mask.size).tolist()
        segmentations.append(segmentation)
    
    return segmentations

# Get "images" and "annotations" info 
def annotate_masks(maskpath, destpath):
    # This id will be automatically increased as we go
    annotation_id = 0
    image_id = 0
    print("maskpath", maskpath)
    for mask_image in glob.glob(maskpath + "\*.tif"):
        original_file_name = os.path.basename(mask_image)
        print(original_file_name)
        # Open the image and (to be sure) we convert it to RGB
        mask_image_open = Image.open(mask_image).convert("RGB")
        w, h = mask_image_open.size

        sub_masks = create_sub_masks(mask_image_open, w, h)
        for color, sub_mask in sub_masks.items():
            try:
                category_id = category_colors[color]
            except Exception as e:
                print(original_file_name, e, mask_image_open.mode)
                # print the distribution of colors in the image
                #print(mask_image_open.getcolors())
                break

            segmentations = create_sub_mask_annotation(sub_mask)
            
            

            annotation_id += 1
        image_id += 1
    return image_id, annotation_id

def normalize_segmentaion(seg, size):
    width, height = size
    arr1 = seg[::2]
    arr2 = seg[1::2]

    arr1 = arr1 / width
    arr2 = arr2 / height

    result = np.empty(seg.size, dtype=arr1.dtype)
    result[::2] = arr1
    result[1::2] = arr2
    return result
#%%
if __name__ == "__main__":
    src = r"D:\datasets\1img"
    src_images = os.path.join(src, "images")
    src_masks = os.path.join(src, "masks")
    dest = r"D:\datasets\1img-yolo"
    if not os.path.exists(dest): os.mkdir(dest)
    dest_images = os.path.join(dest, "images")
    dest_labels = os.path.join(dest, "labels")
    
    IGNORE_BACKGROUND = True
    background_color = "(0, 0, 0)"
    if IGNORE_BACKGROUND:
        category_ids.pop("background")
        category_colors.pop(background_color)

    # copy images
    if not os.path.exists(dest_images): os.mkdir(dest_images)
    for root, dirs, files in os.walk(src_images):
        for file in files:
            shutil.copy(os.path.join(root, file), dest_images)

    # convert masks to yolo format
    if not os.path.exists(dest_labels): os.mkdir(dest_labels)
    image_cnt, annotation_cnt = annotate_masks(src_masks, dest_labels)
    
    print("Created %d annotations for %d images in folder: %s" % (annotation_cnt, image_cnt, dest_labels))

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
