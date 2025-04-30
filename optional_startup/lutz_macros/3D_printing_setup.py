import asyncio
import time
from ophyd import EpicsSignal
from epics import caput
from epics import caget


class set_detector_to_trigger(Device):
    detector_signal=Cpt(EpicsSignal,'')
    def set_detector_trigger(self,det):
        self.detector_signal.put(det.prefix+'cam1:Trigger')

class set_time(Device):
    pre_trigger_time=Cpt(EpicsSignal,'')
    def set_pre_trigger_time(self,time):
        self.pre_trigger_time.put(time)

class set_direct_beam_position(Device):
    position_signal=Cpt(EpicsSignal,'')
    def set_position(self,position):
        self.position_signal.put(position)

class set_axis_to_trigger(Device):
    RBV = Cpt(EpicsSignal,'.INCN')
    VELO = Cpt(EpicsSignal,'.INDN')
    def set_axis(self,motor):
        self.RBV.put(motor.prefix+'.RBV')
        self.VELO.put(motor.prefix+'.VELO')


def position_trigger_setup(motor,trigger_time='ai9',direct_beam_position='ai10',calc_record_number = 5):
    
    time_pv = 'XF:11ID-CT{ES:1}%s'%trigger_time
    time_desc_pv = time_pv+'.DESC'
    position_pv = 'XF:11ID-CT{ES:1}%s'%direct_beam_position
    position_desc_pv = position_pv+'.DESC'

    calc_base = 'XF:11ID-CT{}DB:1userCalc%s'%calc_record_number
    
    # setup analog inputs
    caput(time_desc_pv,'pre_trigger time [s]')
    caput(position_desc_pv,'direct beam position [mm]')

    # setup calc record
    caput('XF:11ID-CT{}DB:1userCalcEnable.VAL',1) # make sure calc records are enabled
    caput(calc_base+'.INAN',time_pv)
    caput(calc_base+'.INBN',position_pv)
    caput(calc_base+'.INCN',motor.prefix+'.RBV')
    caput(calc_base+'.INDN',motor.prefix+'.VELO')
    caput(calc_base+'.CALC','B-A*D<=C')
    caput(calc_base+'.SCAN',9) # scan @.1s
    caput(calc_base+'.ODLY',0.0) # no output delay
    caput(calc_base+'.OOPT',5) # output on transition to non-zero
    detector_pv = calc_base+'.OUTN'

    ret_dict = {'time_pv':time_pv,'position_pv':position_pv,'detector_pv':detector_pv,'motor_pv':calc_base}
    
    manual_trigger = set_detector_to_trigger(ret_dict['detector_pv'],name = 'manual_trigger')
    manual_trigger_time =  set_time(ret_dict['time_pv'],name = 'manual_trigger_time')
    manual_trigger_position = set_direct_beam_position(ret_dict['position_pv'],name = 'manual_trigger_position')
    manual_trigger_axis = set_axis_to_trigger(ret_dict['motor_pv'],name = 'manual_trigger_axis')
    
    
    return manual_trigger,manual_trigger_time, manual_trigger_position ,manual_trigger_axis
    
manual_trigger,manual_trigger_time,manual_trigger_position,  manual_trigger_axis  =  position_trigger_setup(printer.x_head) # setup with diff.xh as default -> need the return dictionary to dynamically create the classes below (ai and calc record number depend on setup!)  


