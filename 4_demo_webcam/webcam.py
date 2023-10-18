#%%
import cv2
from detectron2 import model_zoo
from detectron2.engine import DefaultPredictor
from detectron2.config import get_cfg
from detectron2.utils.visualizer import Visualizer, ColorMode
from detectron2.data import MetadataCatalog
from detectron2.data.datasets import register_coco_instances
from detectron2.data import DatasetCatalog, MetadataCatalog
from detectron2.structures import Instances
#%%
keypoint_names = ["front"]
keypoint_flip_map = []

register_coco_instances("50img_train", {}, r"D:\datasets\50\50img_coco/annotations/train.json", r"D:\datasets\50\50img_coco/images")
register_coco_instances("50img_val", {}, r"D:\datasets\50\50img_coco/annotations/val.json", r"D:\datasets\50\50img_coco/images/")
MetadataCatalog.get("50img_train").set(keypoint_names=keypoint_names, keypoint_flip_map=keypoint_flip_map)
MetadataCatalog.get("50img_val").set(keypoint_names=keypoint_names, keypoint_flip_map=keypoint_flip_map)


#%%
cfg = get_cfg()
cfg.merge_from_file(model_zoo.get_config_file("COCO-InstanceSegmentation/mask_rcnn_R_50_DC5_3x.yaml"))
#cfg.merge_from_file(model_zoo.get_config_file("COCO-Keypoints/keypoint_rcnn_R_50_FPN_3x.yaml"))
#cfg.MODEL.WEIGHTS = model_zoo.get_checkpoint_url("COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_3x.yaml")
cfg.MODEL.WEIGHTS = r"/content/drive/MyDrive/manipulator/evaluation/maskeyrcnn-r50DC5-3x-lr0.001-it1500/model_final.pth"
cfg.OUTPUT_DIR = r"/content/drive/MyDrive/manipulator/evaluation/maskeyrcnn-r50DC5-3x-lr0.001-it1500"
cfg.SOLVER.IMS_PER_BATCH = 15

cfg.MODEL.ROI_HEADS.BATCH_SIZE_PER_IMAGE = 128
cfg.MODEL.ROI_HEADS.NUM_CLASSES = 8
cfg.MODEL.ROI_HEADS.NUM_INSTANCES_PER_IMAGE = 8
cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.7

cfg.MODEL.KEYPOINT_ON = True
cfg.MODEL.MASK_ON = True
cfg.MODEL.ROI_KEYPOINT_HEAD.NUM_KEYPOINTS = 1
cfg.MODEL.ROI_KEYPOINT_HEAD.MIN_KEYPOINTS_PER_IMAGE = 0

cfg.TEST.EVAL_PERIOD = 50
cfg.TEST.KEYPOINT_OKS_SIGMAS = (0.2,)
cfg.TEST.DETECTIONS_PER_IMAGE = 8
cfg.TEST.AUG.ENABLED = True
cfg.TEST.AUG.FLIP = False



cfg.MODEL.WEIGHTS = r"D:\models\detectron2\manipulator\evaluation\maskeyrcnn-r50DC5-3x-lr0.001-it1500\checkpoint_state_dict.pth"
cfg.DATASETS.TRAIN = ("50img_train",)
cfg.DATASETS.TEST = ("50img_val",)
#%%
predictor = DefaultPredictor(cfg)
# overwrite the function _jitter from Visualizer
def _jitter(color):
    return color
# %%
import cv2, queue, threading

class BufferlessVideoCapture:
    def __init__(self, name):
        self.cap = cv2.VideoCapture(name)
        self.q = queue.Queue()
        t = threading.Thread(target=self._reader)
        t.daemon = True
        t.start()

    def _reader(self):
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            if not self.q.empty():
                try:
                    self.q.get_nowait()
                except queue.Empty:
                    pass
            self.q.put(frame)

    def read(self):
        return self.q.get()

def getMaxInstance(outputs):
    max_scores = [0]*8  # Initialize a list of zeros with a size equal to the number of classes
    max_instances = [None]*8  # Initialize a list of None with a size equal to the number of classes
    
    for i in range(len(outputs["instances"])):
        class_id = outputs["instances"].pred_classes[i].item()
        score = outputs["instances"].scores[i].item()
        if score > max_scores[class_id]:
            max_scores[class_id] = score
            max_instances[class_id] = outputs["instances"][i]
    
    max_instances = [instance for instance in max_instances if instance is not None]  # Remove None values
    if max_instances:
        return Instances.cat(max_instances)
    else:
        return outputs["instances"]
#%%
cap = BufferlessVideoCapture(0)
#%%
while True:
    frame = cap.read()
    outputs = predictor(frame)
    outputs["instances"] = getMaxInstance(outputs)
    metadata = MetadataCatalog.get(cfg.DATASETS.TRAIN[0])
    metadata.set(thing_colors=[(255, 0, 0), (255, 255, 0), (128, 0, 255), (255, 128, 0), (0, 0, 255), (128, 255, 255), (0, 255, 0), (128, 128, 128)])
    v = Visualizer(frame[:, :, ::-1], metadata, scale=1.2, instance_mode=ColorMode.SEGMENTATION)
    v._jitter = _jitter
    v = v.draw_instance_predictions(outputs["instances"].to("cpu"))
    out = v.get_image()[:, :, ::-1]
    cv2.imshow("frame", out)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
cv2.destroyAllWindows()
# %%
