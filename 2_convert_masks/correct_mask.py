# %%
import cv2
import numpy as np
import os
from PIL import Image
from scipy.spatial import distance

def increase_hsv(mask_folder):
    colors = np.array([(0, 255, 255), (30, 255, 255), (135, 255, 255), (15, 255, 255), (120, 255, 255), (90, 127, 255), (60, 255, 255), (0, 0, 128), (0, 0, 0)])
    colors_nosat = np.array([(0, 255), (30, 255), (135, 255), (15, 255), (120, 255), (90, 255), (60, 255), (0, 128), (0, 0)])
    for root, dirs, files in os.walk(mask_folder):
        for file in files:
            if file.endswith(".tif"):
                print(os.path.join(root, file))
                img = Image.open(os.path.join(root, file))
                hsv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2HSV)

                hsv_img[hsv_img[:, :, 2] < 5, :] = 0

                # Calculate the error for each color in the list
                errors = distance.cdist(hsv_img.reshape(-1, 3), colors, 'cityblock')
                # Get the color with the smallest error
                best_colors = colors[errors.argmin(axis=1)]
                # Reshape back to the original image shape and convert to 8-bit
                hsv_img = (best_colors.reshape(hsv_img.shape) + 0.5).astype(np.uint8)
                
                

                # Convert back to BGR
                img = cv2.cvtColor(hsv_img, cv2.COLOR_HSV2BGR)
                img = np.where((img==127) | (img==254), img+1, img)
                cv2.imwrite(os.path.join(root, file), img)

increase_hsv(r"D:\datasets\50\50img\masks")
# %%=