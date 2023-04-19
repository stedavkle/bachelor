#%%
import time
import os
import serial
import serial.tools.list_ports

import warnings

class nanocontrol():
    def __init__(self, port):
        self.port = port
        self.ser = serial.Serial(self.port, 115200, timeout=10)
    def close():
        self.ser.close()
    
    # The NanoControl sends a carriage return terminated line after execution of a command:
    # <status char><tab><message string><CR>
    # <status char> can have one of the following values:
    # ‘o’ for okay, ‘e’ for error, ‘i’ for info (e.g. Piezo Voltage Breakdown)
    def __return_handling(func):
            def func_wrapper(*arg, **kwargs):
                res = func(*arg, **kwargs)
                status = res[0]
                message = res[2:-1]
                if status == 'e':
                    raise Exception(message)
                elif status == 'i':
                    warnings.warn(message)
                return message
            return func_wrapper 
    @__return_handling
    def __send(self, cmd):
        leftover = self.ser.inWaiting()
        self.ser.flushInput()
        self.ser.write((cmd + '\r').encode('utf-8'))
        self.ser.flush()
        time.sleep(1)
        buffer = self.ser.read_until(b'\r').decode('ascii')
        #print(buffer)
        return buffer


    # Stops any commands that are currently being executed by the NanoControl. Command itself returns an output. Thus two outputs are returned. Output from the stopped command and from stop.
    # If ack is False, stop command itself returns no acknowledgement
    def stop(self, ack=True):
        if ack:
            return self.__send('stop')
        else:
            return self.__send('stopnack')
    def getVersion(self):
        return self.__send('version')
    def getInfo(self):
        ret = self.__send('knbus ?').split(' ')
        return {'id' : ret[0], 'rank' : ret[1], 'slottype' : ret[2]}

    # Returns values of coarse step counters for channels A to D in <message string> separated by blank if axis not specified or returns value of coarse step counter in <message string>
    def getCoarseCounters(self, axis = None):
        if axis is None:
            ret = self.__send('coarse ?').split(' ')
            return {'A' : ret[0], 'B' : ret[1], 'C' : ret[2], 'D' : ret[3]}
        else:
            assert axis in 'ABCD', 'Axis must be A, B, C or D'
            ret = self.__send('coarse %s ?' % axis)
            return {axis : int(ret[1])}
    # Executes <-65536.. 65535> coarse steps in channel <A.. D> at specified speed <1..6> if speed not specified, executes at current speed.
    # TODO: sending speed does not work
    def moveCoarse(self, axis, steps, speed = None):
        assert axis in 'ABCD', 'Axis must be A, B, C or D'
        assert steps in range(-65536, 65535), 'Steps must be between -65536 and 65535'
        if speed is None:
            return self.__send('coarse %s %s' % (axis, steps))
        else:
            assert speed in range(1, 7), 'Speed must be between 1 and 6'
            return self.__send('coarse %s %s %s' % (axis, steps, speed))
    # Resets coarse step counter in channel <A.. D> (no parameter resets all counters)
    def resetCoarseCounter(self, axis = None):
        if axis:
            assert axis in 'ABCD', 'Axis must be A, B, C or D'
            return self.__send('coarsereset %s' % axis)
        else:
            return self.__send('coarsereset')
    # Returns fine positions for all channels or fine position for specified channel
    def getFinePos12Bit(self, axis = None):
        if axis is None:
            ret = self.__send('fine ?').split(' ')
            return {'A' : ret[0], 'B' : ret[1], 'C' : ret[2], 'D' : ret[3]}
        else:
            assert axis in 'ABCD', 'Axis must be A, B, C or D'
            ret = self.__send('fine %s ?' % axis)
            return {axis : int(ret)}
    def getFinePos16Bit(self, axis = None):
        if axis is None:
            ret = self.__send('fine16 ?').split(' ')
            return {'A' : ret[0], 'B' : ret[1], 'C' : ret[2], 'D' : ret[3]}
        else:
            assert axis in 'ABCD', 'Axis must be A, B, C or D'
            ret = self.__send('fine16 %s ?' % axis)
            return {axis : int(ret)}
    def getFinePosVoltage(self, axis = None):
        if axis is None:
            ret = self.__send('fineu ?').split(' ')
            return {'A' : ret[0], 'B' : ret[1], 'C' : ret[2], 'D' : ret[3]}
        else:
            assert axis in 'ABCD', 'Axis must be A, B, C or D'
            ret = self.__send('fineu %s ?' % axis)
            return {axis : int(ret)}
    # Sets fine position to <-2048.. 2047> in channel <A.. D>
    def setFinePos12Bit(self, axis, position):
        assert axis in 'ABCD', 'Axis must be A, B, C or D'
        assert position in range(-2048, 2047+1), 'Position must be in [-2048, 2047]'
        return self.__send('fine %s %s' % (axis, position))
    # Sets fine position to <-32768.. 32767> in channel <A.. D>
    def setFinePos16Bit(self, axis, position):
        assert axis in 'ABCD', 'Axis must be A, B, C or D'
        assert position in range(-32768, 32767+1), 'Position must be in [-32768, 32767]'
        return self.__send('fine16 %s %s' % (axis, position))
    # Sets fine position to <-80000.. 80000> in channel <A.. D>
    def setFinePosVoltage(self, axis, position):
        assert axis in 'ABCD', 'Axis must be A, B, C or D'
        assert position in range(-80000, 80000+1), 'Position must be in [-80000, 80000]'
        return self.__send('fineu %s %s' % (axis, position))
    # Performs a relative movement of the fine position by the set number of digits <-2048.. 2047> in channel <A.. D>
    def moveFine12Bit(self, axis, steps):
        assert axis in 'ABCD', 'Axis must be A, B, C or D'
        assert steps in range(-2048, 2047+1), 'Steps must be in [-2048, 2047]'
        return self.__send('finestep %s %s' % (axis, steps))
    # Performs a relative movement of the fine position by the set number of digits <-32768.. 32767> in channel <A.. D>
    def moveFine16Bit(self, axis, steps):
        assert axis in 'ABCD', 'Axis must be A, B, C or D'
        assert steps in range(-32768, 32767+1), 'Steps must be in [-32768, 32767]'
        return self.__send('finestep16 %s %s' % (axis, steps))
    # Changes to speed <1.. 6>
    def setSpeed(self, s):
        assert s in range(1, 7), 'Speed must be in [1,6]'
        return self.__send('speed %s' % s)
    # Returns current speed in <message string>
    def getSpeed(self):
        ret = self.__send('speed ?').split(' ')
        return {'speed' : int(ret[0]), 'A' : ret[1], 'B' : ret[2], 'C' : ret[3], 'D' : ret[4]}
    
    # Sets the number of fine or coarse steps to be executed for speed <1.. 6> in channels A to D.
    # TODO: is a dict the best way to do this? maybe a list of tuples?
    def moveAxes(self, movement, speed):
        assert len(movement) == 4, 'Instruction must be dict of length 4'
        assert all([axis in 'ABCD' for axis in movement.keys()]), 'Axis must be A, B, C or D'
        assert all([steps[0] in 'cf' and steps[1] in range(1, 65) for steps in movement.values()]), 'Steps must be coarse/fine and in range [1,64]'
        assert speed in range(1, 7), 'Speed must be in [1,6]'
        cmd = 'speed %s' % speed
        for axis, move in dict.items():
            cmd += ' %s%s' % (move[0], '0' * (2 - len(str(move[1]))) + str(move[1]))
        return self.__send(cmd)
    #Simulates turning the knobs by the specified amount of ticks.
    # TODO: how many ticks are allowed?, how many ticks are one rotation?
    def turnKnobs(self, a, b, c, d):
        assert a in range(-64, 64), 'Knob A must be in [-64, 63]'
        assert b in range(-64, 64), 'Knob B must be in [-64, 63]'
        assert c in range(-64, 64), 'Knob C must be in [-64, 63]'
        assert d in range(-64, 64), 'Knob D must be in [-64, 63]'
        cmd = 'knob %s %s %s %s' % (a, b, c, d)
        return self.__send(cmd)
    # Steps in the range <-100.. +100> for each channel are executed at the current speed. Will use fine with coarse if it is enabled.
    def moveAxesFWC(self, a, b, c, d):
        # range is -100 to 100
        assert a in range(-100, 101), 'Steps A must be in [-100, 100]'
        assert b in range(-100, 101), 'Steps B must be in [-100, 100]'
        assert c in range(-100, 101), 'Steps C must be in [-100, 100]'
        assert d in range(-100, 101), 'Steps D must be in [-100, 100]'
        return self.__send('channel %s %s %s %s' % (a, b, c, d))
    # Steps in the range <-100.. +100> for each channel are executed every few milliseconds <ms> at the current speed. Loop will
    def moveAxisContinuousFWC(self, a, b, c, d, ms):
        # range is -100 to 100
        assert a in range(-100, 101), 'Steps A must be in [-100, 100]'
        assert b in range(-100, 101), 'Steps B must be in [-100, 100]'
        assert c in range(-100, 101), 'Steps C must be in [-100, 100]'
        assert d in range(-100, 101), 'Steps D must be in [-100, 100]'
        assert ms in range(1, 1000), 'Time must be in [1, 999]'
        return self.__send('channel %s %s %s %s %s' % (a, b, c, d, ms))

class controller():
    ncs = {}
    def __init__(self):
        ports = serial.tools.list_ports.comports()
        for port in ports:
            if "N6" in port.serial_number:
                nc = nanocontrol(port.device)
                self.ncs[nc.getInfo()['id']] = nc
    def closeAll(self):
        for nc in self.ncs.values():
            nc.close()

    def retractZigZag(self, tipID, c_goal):
        nc = nanocontrol()#self.ncs[tipID]
        c_init = 0
        while c_init < c_goal:
            nc.


    
# %%
