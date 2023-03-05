#%%
import sys
from win32com.client import makepy, Dispatch
import time

DATASET = r"D:\datasets\test2"
MASK_DETECTOR = "Aux 1"

def init():
    sys.argv = ["makepy", r"CZ.EmApiCtrl.1"]
    makepy.main()

    ocx = Dispatch("CZ.EMApiCtrl.1")
    ocx.InitialiseRemoting()
    return ocx

def getParameters(ocx):
    mag = ocx.Get("AP_MAG", 0)[1]
    wd = ocx.Get("AP_WD", 0)[1] # in meter
    rot = ocx.Get("AP_SCANROTATION", 0)[1]
    detector = ocx.Get("DP_DETECTOR_CHANNEL", '')[1]
    scanrate = ocx.Get("DP_SCANRATE", '')[1]
    return mag, rot, detector, scanrate, wd

def grabImage(ocx):
    mag, rot, detector, scanrate, wd = getParameters(ocx)
    dest = DATASET + r"\train" + toFilename(mag, wd, rot, detector, scanrate)
    #print(dest)
    ocx.Set("DP_FREEZE_ON", "End Frame")
    print('Waiting for image... %s seconds' % str((ocx.Get('AP_FRAME_TIME', 0)[1])/1000 + 1))
    time.sleep((ocx.Get('AP_FRAME_TIME', 0)[1])/1000 + 5)
    ocx.Grab(0, 0, 1024, 768, 0, dest)
    ocx.Execute("CMD_UNFREEZE_ALL")
    print('Image saved')
def grabMask(ocx):
    # scan speed 10-12
    mag, rot, detector, scanrate, wd = getParameters(ocx)
    dest = DATASET + r"\train_mask" + "\mag%s_wd%s_mask.tif" % (ocx.Get("AP_MAG", 0)[1], ocx.Get("AP_WD", 0)[1])
    #print(dest)
    #prev_detector = ocx.Get("DP_DETECTOR_CHANNEL", '')[1]
    prev_scanrate = ocx.Get("DP_SCANRATE", '')[1]
    ocx.Execute('CMD_SCANRATE%s' % 12)
    #ocx.Set("DP_DETECTOR_CHANNEL", MASK_DETECTOR)
    ocx.Set("DP_FREEZE_ON", "End Frame")    
    print('Waiting for mask... %s seconds' % str((ocx.Get('AP_FRAME_TIME', 0)[1])/1000 + 1))
    time.sleep((ocx.Get('AP_FRAME_TIME', 0)[1])/1000 + 5)
    ocx.Grab(0, 0, 1024, 768, 0, dest)
    ocx.Execute("CMD_UNFREEZE_ALL")
    #ocx.Set("DP_DETECTOR_CHANNEL", prev_detector)
    ocx.Set("DP_SCANRATE", prev_scanrate)
    print('Mask saved')

def toFilename(mag, wd, rot, detector, scanrate):
    return "\mag%s_wd%s_scanrot%s_detector%s_scanrate%s.tif" % (mag, wd, rot, detector, scanrate)

# %%
def mag_helper(ocx, mag, rotation, detector, scanrate, wd):
    if len(mag) == 0:
        return
    ocx.Set("AP_MAG", mag[0])
    rotation_helper(ocx, rotation, detector, scanrate, wd)
    mag_helper(ocx, mag[1:], rotation, detector, scanrate, wd)
def rotation_helper(ocx, rotation, detector, scanrate, wd):
    if len(rotation) == 0:
        return
    ocx.Set("AP_SCANROTATION", rotation[0])
    grabMask(ocx)
    detector_helper(ocx, detector, scanrate, wd)
    rotation_helper(ocx, rotation[1:], detector, scanrate, wd)
def detector_helper(ocx, detector, scanrate, wd):
    if len(detector) == 0:
        return
    ocx.Set("DP_DETECTOR_CHANNEL", detector[0])
    scanrate_helper(ocx, scanrate, wd)
    detector_helper(ocx, detector[1:], scanrate, wd)
def scanrate_helper(ocx, scanrate, wd):
    if len(scanrate) == 0:
        return
    ocx.Execute('CMD_SCANRATE%s' % scanrate[0])
    wd_helper(ocx, wd)
    scanrate_helper(ocx, scanrate[1:], wd)
def wd_helper(ocx, wd):
    if len(wd) == 0:
        return
    ocx.Set("AP_WD", str((wd[0]*1000)))
    print("Mag: %s, Rotation: %s, Detector: %s, Scanrate: %s, WD: %s" % (ocx.Get("AP_MAG", 0)[1], ocx.Get("AP_SCANROTATION", 0)[1], ocx.Get("DP_DETECTOR_CHANNEL", '')[1], ocx.Get("DP_SCANRATE", '')[1], ocx.Get("AP_WD", 0)[1]))
    #input("Press Enter to continue...")
    grabImage(ocx)
    wd_helper(ocx, wd[1:])
    
def imagevar02():
    ocx = init()
    init_mag, init_rot, init_detector, init_scanrate, init_wd = getParameters(ocx)


    wd_deviation = 0.005 # in percent
    mag = [10000, 5000, 1000]#, init_mag/10, init_mag*2]
    rotation = ['0']#, '90', '180', '270']
    detector = ['InLens', 'SE2']
    scanrate = ['1', '2', '3', '6', '8', '10']
    wd = [init_wd, init_wd*(1+wd_deviation), init_wd*(1+2*wd_deviation)]#, init_wd*(1-wd_deviation)]

    mag_helper(ocx, mag, rotation, detector, scanrate, wd)
#%%
if __name__ == "__main__":
    ocx = init()
    wd, scanrot, detector, scanrate = getParameters(ocx)
    print("WD: %s, Scanrot: %s, Detector: %s, Scanrate: %s" % (wd, scanrot, detector, scanrate))
    #grabImage(ocx, "C:\\Users\\Public\\Pictures\\Sample Pictures\\test.tif")