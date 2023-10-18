#%%
import SEM_API_CUSTOM
import time
import os
import itertools

class augmentor():
    def __init__(self, sem) -> None:
        self.sem = sem
        self.sem.SetState("DP_SCAN_ROT", 'On')
        self.running = False
        self.iteration = 0
    
    def setParameters(self, dataset_path, wd_deviation, mags, rotations, detectors, scanrates):
        self.dataset_path = dataset_path
        self.wd_deviation = wd_deviation
        self.mags = mags
        self.rotations = rotations
        self.detectors = detectors
        self.scanrates = scanrates
        self.wds = [self.sem.initial_parameters[-1], self.sem.initial_parameters[-1]*(1+(float(wd_deviation)))]
        self.mask_params = list(itertools.product(self.mags, self.rotations))
        self.image_params = list(itertools.product(self.mags, self.rotations, self.detectors, self.scanrates, self.wds))
        return len(self.mask_params), len(self.image_params)
    def grabMasks(self):
        self.running = True
        if not os.path.exists(os.path.join(self.dataset_path, 'masks')):
            os.mkdir(os.path.join(self.dataset_path, 'masks'))
        for i, (mag, rot) in enumerate(self.mask_params):
            if not self.running:
                exit()
            # print(mag, rot)
            #image_path = os.path.join(self.dataset_path, 'masks', 'mag%s_rot%s.tif' % (mag,rot))
            image_path = os.path.join(self.dataset_path, 'masks', '%s_mag%s_rot%s.tif' % (self.iteration, mag, rot))
            print(image_path)
            print(image_path, mag, rot, 'InLens', '10', self.sem.initial_parameters[4])
            self.sem.grabImageWithParameters(image_path, mag, rot, 'InLens', '10', self.sem.initial_parameters[4])
        self.running = False
    def grabImages(self):
        self.running = True
        if not os.path.exists(os.path.join(self.dataset_path, 'images')):
            os.mkdir(os.path.join(self.dataset_path, 'images'))
        for i, (mag, rot, detector, scanrate, wd) in enumerate(self.image_params):
            if not self.running:
                exit()
            # print(i)
            # print(mag, rot, detector, scanrate, wd)
            #image_path = os.path.join(self.dataset_path, 'images', 'mag%s_rot%s_d%s_sr%s_wd%s.tif' % (mag, rot, detector, scanrate, wd))
            image_path = os.path.join(self.dataset_path, 'images', '%s_mag%s_rot%s_%s.tif' % (self.iteration, mag, rot, i))
            self.sem.grabImageWithParameters(image_path, mag, rot, detector, scanrate, wd)
        self.running = False
    def grabRoutine(self):
        self.grabMasks()
        self.grabImages()
        self.iteration += 1
        
    def wait(self, seconds):
        print('Waiting for %s seconds' % seconds)
        time.sleep(seconds)



# dataset_path = r"D:\datasets\automated"

# wd_deviation = 0.005 # in percent
# mag = [5000, 1000, 10000]
# rotation = ['0', '45']
# detector = ['InLens', 'SE2']
# scanrate = ['1', '3', '5', '8']
# #wd = [sem.initial_parameters[-1], sem.initial_parameters[-1]*(1+wd_deviation)]
# wd = [0.5, 0.5*(1+wd_deviation)]
