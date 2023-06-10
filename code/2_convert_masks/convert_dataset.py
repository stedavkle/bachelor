# this code is modified to fit the needs of this project.
# https://github.com/ultralytics/JSON2YOLO
# https://github.com/chrise96/image-to-coco-json-converter

#%%
import os
import cv2
import warnings
import numpy as np
import shutil
from pathlib import Path
from PIL import Image                                      # (pip install Pillow)
from skimage import measure                                # (pip install scikit-image)
from shapely.geometry import Polygon, MultiPolygon         # (pip install Shapely)
import json
from collections import defaultdict
from tqdm import tqdm
import argparse


# SPLIT stuff
def make_split_dirs(dir='new_dir/'):
    # Create folders
    dir = Path(dir)
    if dir.exists():
        shutil.rmtree(dir)  # delete dir
    for p in dir, dir / 'train', dir / 'train_masks', dir / 'val', dir / 'val_masks':
        p.mkdir(parents=True, exist_ok=True)  # make dir
    return dir
def split(path, train_val_split=0.8):
    """
    Split dataset into train and validation sets.
    :param dataset_path: Path to dataset
    :param train_val_split: Percentage of dataset to use for training
    :return: None
    """
    images = os.listdir(path + "/images/")
    train = np.random.choice(images, size=int(len(images) * train_val_split), replace=False)
    val = list(set(images) - set(train))
    return train, val
def create_split_dataset(src, train, val):
    dest = os.path.join(src + '_split')
    make_split_dirs(dest)
    # Copy images and masks to train and val folders
    for file in train:
        shutil.copy(os.path.join(src, 'images', file), os.path.join(dest, 'train'))
        shutil.copy(os.path.join(src, 'masks', file), os.path.join(dest, 'train_masks'))
    for file in val:
        shutil.copy(os.path.join(src, 'images', file), os.path.join(dest, 'val'))
        shutil.copy(os.path.join(src, 'masks', file), os.path.join(dest, 'val_masks'))
    return dest

# COCO stuff
def make_coco_dirs(dir='new_dir/'):
    # Create folders
    dir = Path(dir)
    if dir.exists():
        shutil.rmtree(dir)  # delete dir
    for p in dir, dir / 'images', dir / 'annotations':
        p.mkdir(parents=True, exist_ok=True)  # make dir
    return dir
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
def create_category_annotation(category_dict):
    category_list = []

    for key, value in category_dict.items():
        category = {
            "supercategory": key,
            "id": value,
            "name": key,
            "keypoints" : ["front"],
            "skeleton" : []
        }
        category_list.append(category)

    return category_list
def create_category_annotation_panoptic(category_dict):
    category_list = []

    for key, value in category_dict.items():
        category = {
            "supercategory": key,
            "id": value,
            "isthing": int(value > 0),
            "name": key,
            "color": list(map(int, category_colors_inv[category_ids[key]][1:-1].split(", "))),
            "keypoints" : ["front"],
            "skeleton" : []
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
def create_annotation_format(polygon, segmentation, keypoints, image_id, category_id, annotation_id):
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
    annotation["keypoints"] = [v for point in keypoints for v in point]
    annotation["num_keypoints"] = len(keypoints)
    return annotation
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

def detect_click(event,x,y,flags,param):
    if event == cv2.EVENT_LBUTTONUP:
        param["x"] = x
        param["y"] = y
        param["visible"] = 2
        param["clicked"] = True
    elif event == cv2.EVENT_RBUTTONUP:
        param["x"] = x
        param["y"] = y
        param["visible"] = 1
        param["clicked"] = True
def create_sub_mask_annotation(sub_mask, include_keypoint=False):
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

        keypoints = []
        if include_keypoint:
            cb_params = {"x":0, "y":0, "visible":0, "clicked":False}
            cv2.imshow('image',np.asarray(sub_mask).astype(np.uint8)*255)
            cv2.setMouseCallback('image', detect_click, cb_params)
            while(not cb_params["clicked"]):
                cv2.waitKey(1)
                
            keypoints.append((cb_params["x"], cb_params["y"], cb_params["visible"]))

    return polygons, segmentations, keypoints
def create_segment_format(polygon, category_id, segment_id):
    min_x, min_y, max_x, max_y = polygon.bounds
    width = max_x - min_x
    height = max_y - min_y
    bbox = (min_x, min_y, width, height)
    area = polygon.area

    segment = {
        "id": segment_id,
        "category_id": category_id,
        "iscrowd": 0,
        "bbox": bbox,
        "area": area
    }
    return segment
def images_annotations_info(dataset_path, subset, include_keypoints):
    # This id will be automatically increased as we go
    annotation_id = 0
    image_id = 0
    annotations = []

    annotations_panoptic = []
    
    images = []
    
    for image in tqdm(subset, desc="Creating annotations"):
        segments = []

        # We make a reference to the original file in the COCO JSON file
        original_file_name = os.path.join(image)
        mask_image = os.path.join(dataset_path, 'masks', image)

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
            polygons, segmentations, keypoints = create_sub_mask_annotation(sub_mask, include_keypoints)



            # Check if we have classes that are a multipolygon
            if category_id in multipolygon_ids:
                # Combine the polygons to calculate the bounding box and area
                multi_poly = MultiPolygon(polygons)
                                
                annotation = create_annotation_format(multi_poly, segmentations, keypoints, image_id, category_id, annotation_id)
                segments.append(create_segment_format(multi_poly, category_id, annotation_id))
                annotations.append(annotation)
                annotation_id += 1
            else:
                for i in range(len(polygons)):
                    # Cleaner to recalculate this variable
                    segmentation = [np.array(polygons[i].exterior.coords).ravel().tolist()]
                    
                    annotation = create_annotation_format(polygons[i], segmentation, keypoints, image_id, category_id, annotation_id)
                    segments.append(create_segment_format(polygons[i], category_id, annotation_id))
                    annotations.append(annotation)
                    annotation_id += 1
        annotations_panoptic.append({
            "image_id": image_id,
            "file_name": original_file_name,
            "segments_info": segments
        })
        image_id += 1
    return images, annotations, annotations_panoptic, annotation_id



def create_coco_dataset(dataset_path, train, val, include_keypoints):
    train_coco_format = get_coco_json_format()
    val_coco_format = get_coco_json_format()

    train_coco_format_panoptic = get_coco_json_format()
    val_coco_format_panoptic = get_coco_json_format()

    train_coco_format["categories"] = create_category_annotation(category_ids)
    val_coco_format["categories"] = create_category_annotation(category_ids)

    train_coco_format_panoptic["categories"] = create_category_annotation_panoptic(category_ids)
    val_coco_format_panoptic["categories"] = create_category_annotation_panoptic(category_ids)

    train_images, train_annotations, train_annotations_panoptic, train_annotation_id = images_annotations_info(dataset_path, train, include_keypoints)
    val_images, val_annotations, val_annotations_panoptic, val_annotation_id = images_annotations_info(dataset_path, val, include_keypoints)

    train_coco_format["images"], train_coco_format["annotations"], train_annotation_cnt = train_images, train_annotations, train_annotation_id
    val_coco_format["images"], val_coco_format["annotations"], val_annotation_cnt = val_images, val_annotations, val_annotation_id

    train_coco_format_panoptic["images"], train_coco_format_panoptic["annotations"], train_annotation_cnt = train_images, train_annotations_panoptic, train_annotation_id
    val_coco_format_panoptic["images"], val_coco_format_panoptic["annotations"], val_annotation_cnt = val_images, val_annotations_panoptic, val_annotation_id

    dest = dataset_path + '_coco'
    make_coco_dirs(dest)

    dest_panoptic = dataset_path + '_coco_panoptic'
    make_coco_dirs(dest_panoptic)
    
    with open(os.path.join(dest,  'annotations', 'train.json'), "w") as outfile:
            json.dump(train_coco_format, outfile)
    with open(os.path.join(dest,  'annotations', 'val.json'), "w") as outfile:
            json.dump(val_coco_format, outfile)

    with open(os.path.join(dest_panoptic,  'annotations', 'train.json'), "w") as outfile:
            json.dump(train_coco_format_panoptic, outfile)
    with open(os.path.join(dest_panoptic,  'annotations', 'val.json'), "w") as outfile:
            json.dump(val_coco_format_panoptic, outfile)

    # copy images folder to coco folder
    shutil.copytree(os.path.join(dataset_path, 'images'), os.path.join(dest, 'images'), dirs_exist_ok=True)
    shutil.copytree(os.path.join(dataset_path, 'images'), os.path.join(dest_panoptic, 'images'), dirs_exist_ok=True)

    shutil.copytree(os.path.join(dataset_path, 'masks'), os.path.join(dest_panoptic, 'annotations', 'masks'), dirs_exist_ok=True)

    print("Created %d annotations for train images:" % (train_annotation_cnt))
    print("Created %d annotations for val images:" % (val_annotation_cnt))
    return dest, dest_panoptic

# YOLO stuff
def make_yolo_dirs(dir='new_dir/'):
    # Create folders
    dir = Path(dir)
    if dir.exists():
        shutil.rmtree(dir)  # delete dir
    for p in dir, dir / 'train', dir / 'val':
        p.mkdir(parents=True, exist_ok=True)  # make dir
    return dir
def min_index(arr1, arr2):
    """Find a pair of indexes with the shortest distance. 
    Args:
        arr1: (N, 2).
        arr2: (M, 2).
    Return:
        a pair of indexes(tuple).
    """
    dis = ((arr1[:, None, :] - arr2[None, :, :]) ** 2).sum(-1)
    return np.unravel_index(np.argmin(dis, axis=None), dis.shape)
def merge_multi_segment(segments):
    """Merge multi segments to one list.
    Find the coordinates with min distance between each segment,
    then connect these coordinates with one thin line to merge all 
    segments into one.

    Args:
        segments(List(List)): original segmentations in coco's json file.
            like [segmentation1, segmentation2,...], 
            each segmentation is a list of coordinates.
    """
    s = []
    segments = [np.array(i).reshape(-1, 2) for i in segments]
    idx_list = [[] for _ in range(len(segments))]

    # record the indexes with min distance between each segment
    for i in range(1, len(segments)):
        idx1, idx2 = min_index(segments[i - 1], segments[i])
        idx_list[i - 1].append(idx1)
        idx_list[i].append(idx2)

    # use two round to connect all the segments
    for k in range(2):
        # forward connection
        if k == 0:
            for i, idx in enumerate(idx_list):
                # middle segments have two indexes
                # reverse the index of middle segments
                if len(idx) == 2 and idx[0] > idx[1]:
                    idx = idx[::-1]
                    segments[i] = segments[i][::-1, :]

                segments[i] = np.roll(segments[i], -idx[0], axis=0)
                segments[i] = np.concatenate([segments[i], segments[i][:1]])
                # deal with the first segment and the last one
                if i in [0, len(idx_list) - 1]:
                    s.append(segments[i])
                else:
                    idx = [0, idx[1] - idx[0]]
                    s.append(segments[i][idx[0]:idx[1] + 1])

        else:
            for i in range(len(idx_list) - 1, -1, -1):
                if i not in [0, len(idx_list) - 1]:
                    idx = idx_list[i]
                    nidx = abs(idx[1] - idx[0])
                    s.append(segments[i][nidx:])
    return s
def create_yolo_dataset(dataset_path, train, val, use_segments=True):
    dest = dataset_path + '_yolo'
    coco_dataset_path = dataset_path + '_coco'
    if not os.path.exists(coco_dataset_path):
        warnings.warn('No COCO dataset exists. running create_coco_dataset()')
        coco_dataset_path = create_coco_dataset(coco_dataset_path)


    save_dir = make_yolo_dirs(Path(coco_dataset_path.replace('coco', 'yolo')))  # output directory
    json_dir = Path(coco_dataset_path, 'annotations')  # coco json directory
    
    # Import json
    for json_file in sorted(Path(json_dir).resolve().glob('*.json')):
        fn = Path(save_dir) / json_file.stem.replace('instances_', '') / 'labels'  # folder name
        fn.mkdir()
        fn2 = Path(save_dir) / json_file.stem.replace('instances_', '') / 'images'
        fn2.mkdir()

        with open(json_file) as f:
            data = json.load(f)

        # Create image dict
        images = {'%g' % x['id']: x for x in data['images']}
        # Create image-annotations dict
        imgToAnns = defaultdict(list)
        for ann in data['annotations']:
            imgToAnns[ann['image_id']].append(ann)

        # Write labels file
        for img_id, anns in tqdm(imgToAnns.items(), desc=f'Annotations {json_file}'):
            img = images['%g' % img_id]
            h, w, f = img['height'], img['width'], img['file_name']

            shutil.copy(os.path.join(dataset_path, 'images', f), os.path.join(dest, json_file.stem.replace('instances_', ''), 'images'))

            bboxes = []
            segments = []
            for ann in anns:
                if ann['iscrowd']:
                    continue
                # The COCO box format is [top left x, top left y, width, height]
                box = np.array(ann['bbox'], dtype=np.float64)
                box[:2] += box[2:] / 2  # xy top-left corner to center
                box[[0, 2]] /= w  # normalize x
                box[[1, 3]] /= h  # normalize y
                if box[2] <= 0 or box[3] <= 0:  # if w <= 0 and h <= 0
                    continue
                if IGNORE_BACKGROUND:
                    cls = ann['category_id'] - 1
                else:
                    cls = ann['category_id']  # class
                box = [cls] + box.tolist()
                if box not in bboxes:
                    bboxes.append(box)
                # Segments
                if use_segments:
                    if len(ann['segmentation']) > 1:
                        s = merge_multi_segment(ann['segmentation'])
                        s = (np.concatenate(s, axis=0) / np.array([w, h])).reshape(-1).tolist()
                    else:
                        s = [j for i in ann['segmentation'] for j in i]  # all segments concatenated
                        s = (np.array(s).reshape(-1, 2) / np.array([w, h])).reshape(-1).tolist()
                    s = [cls] + s
                    if s not in segments:
                        segments.append(s)

            # Write
            with open((fn / f).with_suffix('.txt'), 'a') as file:
                for i in range(len(bboxes)):
                    line = *(segments[i] if use_segments else bboxes[i]),  # cls, box or segments
                    file.write(('%g ' * len(line)).rstrip() % line + '\n')
    return dest
# Label ids of the dataset
category_ids = {
    "background": 0,
    "tip1": 1,
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


# Define the ids that are a multiplolygon. In our case: wall, roof and sky
multipolygon_ids = [0, 1, 2, 3, 4, 5, 6, 7, 8]
#%%
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    #parser.add_argument('-h', type)
    parser.add_argument('-dataset', required=True, type=str, help='dataset path (ie: /home/user/dataset)')
    parser.add_argument('-split', required=True, type=float, help='split ratio (ie: 0.8)')
    parser.add_argument('-coco', action='store_true', help='convert to coco dataset')
    parser.add_argument('-yolo', action='store_true', help='convert to yolo dataset')
    parser.add_argument('-oc', action='store_true', help='use one class, all tips are the same class')
    parser.add_argument('-ib', action='store_true', help='include background')
    parser.add_argument('-kp', action='store_true', help='include keypoint coordinates')

    args = parser.parse_args()
    print(args)

    if args.oc:
        category_ids = {"background": 0, "tip1": 1}
        category_colors = {"(0, 0, 0)": 0, "(255, 0, 0)": 1, "(255, 255, 0)": 1, "(128, 0, 255)": 1, "(255, 128, 0)": 1, "(0, 0, 255)": 1, "(128, 255, 255)": 1, "(0, 255, 0)": 1, "(128, 128, 128)": 1}
        category_colors_inv = {v: k for k, v in category_colors.items()}


    if args.dataset:
        dataset_path = args.dataset

    IGNORE_BACKGROUND = not args.ib
    background_color = "(0, 0, 0)"
    if IGNORE_BACKGROUND:
        category_ids.pop("background")
        category_colors.pop(background_color)
        multipolygon_ids.remove(0)
#%%
    if args.split:
        print("Splitting dataset...")
        train, val = split(dataset_path, args.split)
        print("Train: ", len(train))
        print("Val: ", len(val))

    #%%
        split_dir = create_split_dataset(dataset_path, train, val)
        print("Split dataset created at: ", split_dir)    
#%%
    if args.kp:
        cv2.namedWindow('image', cv2.WINDOW_NORMAL)
        cv2.setWindowProperty('image', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    if args.coco:
        print("Creating coco dataset...")
        coco_dir, coco_panoptic_dir = create_coco_dataset(dataset_path, train, val, args.kp)
        print("Coco dataset created at: ", coco_dir)
        print("Coco panoptic dataset created at: ", coco_panoptic_dir)
# %%
    if args.yolo:
        print("Creating yolo dataset...")
        yolo_dir = create_yolo_dataset(dataset_path, train, val)
        print("Yolo dataset created at: ", dataset_path)
