#%%
import json

def merge_coco_files(json_files, output_file):
    merged_data = {
        "images": [],
        "annotations": [],
        "categories": []
    }

    image_id_offset = 0
    annotation_id_offset = 0

    for json_file in json_files:
        with open(json_file) as f:
            data = json.load(f)

        # Calculate new IDs for images and annotations
        for image in data['images']:
            image['id'] += image_id_offset
        for annotation in data['annotations']:
            annotation['id'] += annotation_id_offset
            annotation['image_id'] += image_id_offset

        # Update the data lists
        merged_data['images'] += data['images']
        merged_data['annotations'] += data['annotations']
        merged_data['categories'] = data['categories']

        # Update the ID offsets for the next file
        image_id_offset = max(image['id'] for image in merged_data['images']) + 1
        annotation_id_offset = max(annotation['id'] for annotation in merged_data['annotations']) + 1

    with open(output_file, 'w') as f:
        json.dump(merged_data, f)

def check_ids(json_file):
    with open(json_file) as f:
        data = json.load(f)

    image_ids = {image['id'] for image in data['images']}
    annotation_ids = [annotation['id'] for annotation in data['annotations']]
    annotation_image_ids = [annotation['image_id'] for annotation in data['annotations']]

    # Check for duplicate IDs
    unique_annotation_ids = set(annotation_ids)
    if len(annotation_ids) != len(unique_annotation_ids):
        print("Error: Duplicate annotation IDs found.")

    # Check for annotations referencing non-existing images
    for annotation_image_id in annotation_image_ids:
        if annotation_image_id not in image_ids:
            print(f"Error: Annotation with image_id {annotation_image_id} has no matching image.")
def check_segments(json_file):
    with open(json_file) as f:
        data = json.load(f)
    print(f"Checking {json_file}")
    for annotation in data['annotations']:
        if 'segmentation' in annotation:
            segments = annotation['segmentation']
            if len(segments) >= 3:
                print(f"Error: Annotation with id {annotation['id']} has more than three segments.")
            for segment in segments:
                if len(segment) < 9:
                    print(f"Error: Annotation with id {annotation['id']} has Segment with less than 5 points.")

#%%
# List of JSON files
json_files = [r"D:\datasets\merged\annotations\50train.json", r"D:\datasets\merged\annotations\100train.json", r"D:\datasets\merged\annotations\600train.json"]
json_val_files = [r"D:\datasets\merged\annotations\50val.json", r"D:\datasets\merged\annotations\100val.json", r"D:\datasets\merged\annotations\600val.json"]
# Output file
output_file = r"D:\datasets\merged\annotations\train.json"
output_val_file = r"D:\datasets\merged\annotations\val.json"

merge_coco_files(json_files, output_file)
#merge_coco_files(json_val_files, output_val_file)
# %%
check_ids(output_val_file)
check_ids(output_file)
# %%
check_segments(output_val_file)
check_segments(output_file)
# %%
