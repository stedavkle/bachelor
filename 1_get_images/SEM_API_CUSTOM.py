import sys
from win32com.client import makepy, Dispatch
import time
import warnings

_excpetion_dict = \
{1000: ('API_E_GET_TRANSLATE_FAIL',
  'Failed to translate parameter into an id'),
 1001: ('API_E_GET_AP_FAIL', 'Failed to get analogue value'),
 1002: ('API_E_GET_DP_FAIL', 'Failed to get digital value'),
 1003: ('API_E_GET_BAD_PARAMETER',
  'Parameter supplied is not analogue nor digital'),
 1004: ('API_E_SET_TRANSLATE_FAIL',
  'Failed to translate parameter into an id'),
 1005: ('API_E_SET_STATE_FAIL', 'Failed to set a digital state'),
 1006: ('API_E_SET_FLOAT_FAIL', 'Failed to set a float value'),
 1007: ('API_E_SET_FLOAT_LIMIT_LOW', 'Value supplied is too low'),
 1008: ('API_E_SET_FLOAT_LIMIT_HIGH', 'Value supplied is too high'),
 1009: ('API_E_SET_BAD_VALUE', 'Value supplied is is of wrong type'),
 1010: ('API_E_SET_BAD_PARAMETER',
  'Parameter supplied is not analogue nor digital'),
 1011: ('API_E_EXEC_TRANSLATE_FAIL', 'Failed to translate command into an id'),
 1012: ('API_E_EXEC_CMD_FAIL', 'Failed to execute command'),
 1013: ('API_E_EXEC_MCF_FAIL', 'Failed to execute file macro'),
 1014: ('API_E_EXEC_MCL_FAIL', 'Failed to execute library macro'),
 1015: ('API_E_EXEC_BAD_COMMAND', 'Command supplied is not implemented'),
 1016: ('API_E_GRAB_FAIL', 'Grab command failed'),
 1017: ('API_E_GET_STAGE_FAIL', 'Get Stage position failed'),
 1018: ('API_E_MOVE_STAGE_FAIL', 'Move Stage position failed'),
 1019: ('API_E_NOT_INITIALISED', 'API not initialised'),
 1020: ('API_E_NOTIFY_TRANSLATE_FAIL',
  'Failed to translate parameter to an id'),
 1021: ('API_E_NOTIFY_SET_FAIL', 'Set notification failed'),
 1022: ('API_E_GET_LIMITS_FAIL', 'Get limits failed'),
 1023: ('API_E_GET_MULTI_FAIL', 'Get multiple parameters failed'),
 1024: ('API_E_SET_MULTI_FAIL', 'Set multiple parameters failed'),
 1025: ('API_E_NOT_LICENSED', 'Missing API license'),
 1026: ('API_E_NOT_IMPLEMENTED', 'Reserved or not implemented'),
 1027: ('API_E_GET_USER_NAME_FAIL',
  'Failed to get user name (Remoting Interface only)'),
 1028: ('API_E_GET_USER_IDLE_FAIL',
  'Failed to get user idle state (Remoting Interface only)'),
 1029: ('API_E_GET_LAST_REMOTING_CONNECT_ERROR_FAIL',
  'Failed to get the last remoting connection error string (Remoting Interface Only)'),
 1030: ('API_E_EMSERVER_LOGON_FAILED',
  'Failed to remotely logon to the EM Server (username and password may be incorrect or EM Server is not running or User is already logged on, Remoting only)'),
 1031: ('API_E_EMSERVER_START_FAILED',
  'Failed to start the EM Server. This may be because the Server is already running or has an internal error (Remoting Interface only)'),
 1032: ('API_E_PARAMETER_IS_DISABLED',
  'The command or parameter is currently disabled (you cannot execute or set it. Remoting Interface only)'),
 2027: ('API_E_REMOTING_NOT_CONFIGURED',
  'Remoting incorrectly configured, use RConfigure to correct'),
 2028: ('API_E_REMOTING_FAILED_TO_CONNECT',
  'Remoting did not connect to the server'),
 2029: ('API_E_REMOTING_COULD_NOT_CREATE_INTERFACE',
  'Remoting could not start (unknown reason)'),
 2030: ('API_E_REMOTING_EMSERVER_NOT_RUNNING',
  'Remoting: Remote server is not running currently'),
 2031: ('API_E_REMOTING_NO_USER_LOGGED_IN',
  'Remoting: Remote server has no user logged in')}
 

# class to handle exceptions
class API_ERROR(Exception):
    def __init__(self, error_code):
        global _excpetion_dict
        self.error_text = ('\n').join(_excpetion_dict[error_code])
        warnings.warn(self.error_text)

class SEM_API_CUSTOM():
    ocx = None
    initial_parameters = None # mag, rot, detector, scanrate, wd
    dataset_path = None
    busy = False

    def __init__(self):
        sys.argv = ["makepy", r"CZ.EmApiCtrl.1"]
        makepy.main()
        self.ocx = Dispatch("CZ.EMApiCtrl.1")

    def __error_handling(func):
            def func_wrapper(*arg, **kwargs):
                res = func(*arg, **kwargs)
                if type(res) == int:
                    return_code = res
                    if return_code != 0:
                        raise API_ERROR(return_code)
                elif type(res) == tuple:
                    return_code = res[0]
                    result = res[1]
                    if return_code == 0:
                        return result
                    else:
                        raise API_ERROR(return_code)
            return func_wrapper

    @__error_handling
    def openConnection(self):
        res = self.ocx.InitialiseRemoting()
    @__error_handling
    def getVersion(self):
        return self.ocx.GetVersion()
    @__error_handling
    def closeConnection(self):
        return self.ocx.ClosingControl()
    def getInitialParameters(self):
        self.initial_parameters = (self.getAPMag(), self.getAPRot(), self.getDPDetector(), self.getDPScanrate(), self.getAPWD())
        print("Initial parameters saved")
        return self.initial_parameters
    def restoreInitialParameters(self):
        self.setAPMag(self.initial_parameters[0])
        self.setAPRot(self.initial_parameters[1])
        self.setDPDetector(self.initial_parameters[2])
        self.setDPScanrate(self.initial_parameters[3])
        self.setAPWD(self.initial_parameters[4])
        self.ocx.Execute("CMD_UNFREEZE_ALL")
        print("All parameters set to initial values")
    @__error_handling
    def Grab(self, fname, X = 0, Y = 0, W = 1024, H = 768, overlay = False):
        """
        The function to grab the current image.
        left, right, top, button defines the desired size of the imaged, express as the 
        coordinate relative to the full image.
        For example, if 10% of the edge should be excluded, the coordinate should be
            left = 0.1, right = 0.9, top = 0,1, button = 0.9
        overlay determines whether the image overlay such as datazone should be included.
        """
        #X = int(left * 1024)
        #Y = int(top * 768)
        #W = int((right-left)*1024)
        #H = int((bottom-top)*768)
        if overlay:
            res = self.ocx.Grab(X,Y,W,H,-1,fname)
        else:
            res = self.ocx.Grab(X,Y,W,H,0,fname)
        return res
    @__error_handling
    def grabFullImage(self, fname, overlay = False):
        """
        grab the current full image by restarting the scan and till the complete
        frame is finished, and then save the image.
        """
        self.SetState("DP_FREEZE_ON", "End Frame")
        self.Execute("CMD_UNFREEZE_ALL")
        time.sleep(0.1)
        #self.Execute("CMD_MODE_NORMAL")
        #time.sleep(0.1)
        if self.GetState("DP_NOISE_REDUCTION") in ("Frame Avg","Line Avg",\
                        "Pixel Avg.", "Continuous Avg.", "Drift Comp. Frame Avg."):
            time.sleep(0.1)
            self.Execute("CMD_FREEZE_ALL")
        while self.GetState("DP_FROZEN") == "Live":
            time.sleep(0.1)
        res = self.Grab(fname, overlay = overlay)
        print('Image saved')
        return res
    def grabImageWithParameters(self, dest, mag, rot, detector, scanrate, wd):
        self.setAPMag(mag)
        self.setAPRot(rot)
        self.setDPDetector(detector)
        self.setDPScanrate(scanrate)
        self.setAPWD(wd)
        self.grabFullImage(dest)
    @__error_handling
    def getAPMag(self):
        return self.ocx.Get("AP_MAG", 0)
    @__error_handling
    def setAPMag(self, mag):
        self.ocx.Set("AP_MAG", str(mag))
    @__error_handling
    def getAPWD(self):
        return self.ocx.Get("AP_WD", 0)
    @__error_handling
    def setAPWD(self, wd):
        self.ocx.Set("AP_WD", float(wd))
    @__error_handling
    def getAPRot(self):
        return self.ocx.Get("AP_SCANROTATION", 0)
    @__error_handling
    def setAPRot(self, rot):
        self.ocx.Set("AP_SCANROTATION", str(rot))
    @__error_handling
    def getDPDetector(self):
        return self.ocx.Get("DP_DETECTOR_CHANNEL", '')
    @__error_handling
    def setDPDetector(self, detector):
        self.ocx.Set("DP_DETECTOR_CHANNEL", str(detector))
    @__error_handling
    def getDPScanrate(self):
        return self.ocx.Get("DP_SCANRATE", '')
    @__error_handling
    def setDPScanrate(self, scanrate):
        self.ocx.Execute('CMD_SCANRATE%s' % str(scanrate))
    @__error_handling
    def getAPFrameTimeInSeconds(self):
        res = self.ocx.Get('AP_FRAME_TIME', 0)
        return (res[0], self.ocx.Get('AP_FRAME_TIME', 0)[1]/1000)

    @__error_handling
    def GetState(self, DP_name, style='string'):
        """
        function to get an digital value.
        style: float or string
        int returns a integer number, string returns a string representation.
        """
        if style == 'int':
            buffer = 0
            res = self.ocx.Get(DP_name, buffer)
            return res
        elif style == 'string':
            buffer = ''
            res = self.ocx.Get(DP_name, buffer)
            return res
        else:
            raise AttributeError("style = int or string")
            
    @__error_handling
    def SetState(self, DP_name, value):
        """
        function to set a digital state.
        The function can take either integer or a formatted string.
        """
        if type(value) == str:
            pass
        else:
            value = int(value)
        res = self.ocx.Set(DP_name, value)
        return res
    @__error_handling
    def Execute(self, CMD_name):
        res = self.ocx.Execute(CMD_name)
        return res