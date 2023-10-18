#%%
import cv2
import numpy as np
import PIL.Image as Image
from skimage import measure                                # (pip install scikit-image)
from shapely.geometry import Polygon, MultiPolygon         # (pip install Shapely
import time
#%%
def detect_click(event,x,y,flags,param):
    global mouseX,mouseY
    if event == cv2.EVENT_LBUTTONUP:
        param["x"] = x
        param["y"] = y
        param["clicked"] = True



#%%
def create_sub_masks(mask_image, width, height):
    # Initialize a dictionary of sub-masks indexed by RGB colors
    sub_masks = {}
    for x in range(width):
        for y in range(height):
            # Get the RGB values of the pixel
            pixel = mask_image.getpixel((x,y))[:3]

            # Check to see if we have created a sub-mask...
            pixel_str = str(pixel)
            if True and pixel_str == "(0, 0, 0)":
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

#%%
times = []
cv2.namedWindow('image', cv2.WINDOW_NORMAL)
cv2.setWindowProperty('image', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
mask = Image.open(r"C:\Users\david\Desktop\50img\masks\6-Punkt-Messung auf 22 nm.tif").convert("RGB")
w, h = mask.size
sub_masks = create_sub_masks(mask, w, h)
for sub_mask in sub_masks:
    start = time.time()
    cb_params = {"x":0, "y":0, "clicked":False}
    cv2.imshow('image',np.asarray(sub_masks[sub_mask]).astype(np.uint8)*255)
    cv2.setMouseCallback('image', detect_click, cb_params)
    while(not cb_params["clicked"]):
        cv2.waitKey(1)
        
    print(cb_params["x"], cb_params["y"])
    times.append(time.time()-start)
cv2.destroyAllWindows()
print(np.mean(times))
# %%
