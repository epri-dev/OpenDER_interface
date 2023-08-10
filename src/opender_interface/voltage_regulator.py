# %%

# -*- coding: utf-8 -*-
"""
Created on Fri Feb  4 13:07:24 2022

@author: pwre002
"""
import numpy as np

#%%

# %%
"""
This is the voltage regulator (VR) control model, this model is used for determining the VR tap within the provided circuit.
"""
class VR_Model(object):

    '''
    Initialize "VR_Model" object, with the obligatory input parameter 'Ts', signifying the sampling time, while other
    parameters are optional.
    '''
    def __init__(self,
                 Ts,  # sampling time (s)
                 Td_ctrl=30,  # delay time for control (s)
                 Td_tap=2,  # delay time for tapping (s)
                 Vref=120,  # reference voltage in 120V base (V)
                 db=2,  # deadband in 120V base (V)
                 LDC_R=0,  # LDC Vr (V)
                 LDC_X=0,  # LDC Vx (V)
                 PT_Ratio=120,  # PT ratio (Vpri/Vsec)
                 CT_Primary=100,  # CT primary rating (A)
                 tap_max=16,  # maximum tap position
                 tap_min=-16,  # minimum tap position
                 tap_ini=0,  # initial tap position
                 ):
        self.Ts = Ts
        self.Td_ctrl = Td_ctrl
        self.Td_tap = Td_tap
        self.Vref = Vref
        self.db = db
        self.LDC_R = LDC_R
        self.LDC_X = LDC_X
        self.PT_Ratio = PT_Ratio
        self.CT_Primary = CT_Primary
        self.tap_max = tap_max
        self.tap_min = tap_min
        self.tap = tap_ini
        # internal state variables
        self.Ti_ctrl = 0
        self.Ti_tap = Td_tap
        self.state = ['Idle', 'OV', 'UV'][0]
        self.total_sw = 0
        self.V = 0

    '''
    Determine VR tap based on given circuit
    '''
    def run(self,
            Vreg=None,  # regulating voltage  (magnitude on 120V base)
            Vpri=[],  # primary voltage (complex number in V)
            Ipri=[],  # primary current (complex number in A)
            ):
        # input conditioning
        if Vreg != None:
            pass
        else:
            Vsec = [x / self.PT_Ratio for x in Vpri]
            if Ipri != []:
                Vldc = [x / self.CT_Primary * (self.LDC_R + 1j * self.LDC_X) for x in Ipri]
            else:
                Vldc = [0 for x in Vpri]
            Vreg = np.mean(np.abs(np.array(Vsec) - np.array(Vldc)))
        self.V = Vreg
            # Hysteresis logic
        if Vreg > self.Vref + self.db / 2:
            if self.state == 'OV':
                self.Ti_ctrl = self.Ti_ctrl + self.Ts
            else:
                self.state = 'OV'
                self.Ti_ctrl = 0
        elif Vreg < self.Vref - self.db / 2:
            if self.state == 'UV':
                self.Ti_ctrl = self.Ti_ctrl + self.Ts
            else:
                self.state = 'UV'
                self.Ti_ctrl = 0
        else:
            self.state = 'Idle'
            self.Ti_ctrl = 0
        # Tap operation
        self.Ti_tap = self.Ti_tap + self.Ts
        if self.Ti_ctrl > self.Td_ctrl:
            if (self.state == 'OV') and (self.Ti_tap >= self.Td_tap):
                if self.tap > self.tap_min:
                    self.tap = self.tap - 1
                    self.Ti_tap = 0
                    self.total_sw += 1
            if (self.state == 'UV') and (self.Ti_tap >= self.Td_tap):
                if self.tap < self.tap_max:
                    self.tap = self.tap + 1
                    self.Ti_tap = 0
                    self.total_sw += 1
        # save internal variable and return tap number
        self.Vreg = Vreg
        return self.tap



