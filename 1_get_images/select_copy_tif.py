import os
import shutil
import cv2
import numpy as np

src = r'D:\original'
dst = r'D:\copy\GeminiSEM300'
if not os.path.exists(dst):
    os.makedirs(dst)

i = 0
cv2.namedWindow('image', cv2.WINDOW_NORMAL)
cv2.setWindowProperty('image', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

filepaths = []

for root, dirs, files in os.walk(src):
    for file in files:
        if file.endswith('.tif'):
            filepaths.append(os.path.join(root, file))


            # src_file = os.path.join(root, file)
            # dst_file = os.path.join(dst, str(i) + '.tif')
            # print(src_file)

            # img = cv2.imread(os.path.join(root, file))
            # cv2.imshow('image', img)
            # k = cv2.waitKey(0)
            # if k & 0xFF == ord('y'):
            #     shutil.copy(src_file, dst_file)
            # if k & 0xFF == ord('q'):
            #     cv2.destroyAllWindows()
            # i += 1q
np.random.shuffle(filepaths)
for file in filepaths:
    src_file = file
    dst_file = os.path.join(dst, str(file).split('\\')[-1])
    print(src_file, dst_file)
    try:
        img = cv2.imread(os.path.join(src, file))
    except:
        continue
    cv2.imshow('image', img)
    k = cv2.waitKey(0)
    if k & 0xFF == ord('b'):
        shutil.copy(src_file, dst_file)
    if k & 0xFF == ord('q'):n
        cv2.destroyAllWindows()
    i += 1  