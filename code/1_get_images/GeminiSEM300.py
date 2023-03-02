import os
from PIL import Image
from PIL.TiffTags import TAGS
import exifread
import tifffile

rem_path = r'R:\images'

for root, dirs, files in os.walk(rem_path):
    for file in files:
        if file.endswith(".tif"):
            # get the type of the file
            try:
                with tifffile.TiffFile(os.path.join(root, file)) as tif:
                    tag_str1 = tif.pages[0].tags[34118].value
                    tag_str2 = tif.pages[0].tags[34119].value

                    tag_dict1 = dict(tag_str1)
                    tag_dict2 = {key.replace('\x00', '').replace('\r', '') : value.replace('\x00', '').replace('\r', '') for key, value in zip(tag_str2.split('\n')[35::2], tag_str2.split('\n')[36::2])}
                    #print(tag_dict2['AP_IMAGE_PIXEL_SIZE'])
            except Exception as e:
                print(os.path.join(root, file))
                print(e)