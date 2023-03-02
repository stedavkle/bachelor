import os
import shutil
import cv2

src = r'D:\original'
dst = r'D:\copy\GeminiSEM300'
if not os.path.exists(dst):
    os.makedirs(dst)

i = 0
for root, dirs, files in os.walk(src):
    for file in files:
        if file.endswith('.tif'):
            src_file = os.path.join(root, file)
            dst_file = os.path.join(dst, str(i) + '.tif')
            print(src_file)

            img = cv2.imread(os.path.join(root, file))
            cv2.imshow('image', img)
            k = cv2.waitKey(0)
            if k & 0xFF == ord('y'):
                shutil.copy(src_file, dst_file)
            cv2.destroyAllWindows()
            i += 1