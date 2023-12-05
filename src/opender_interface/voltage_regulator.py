# Copyright © 2023 Electric Power Research Institute, Inc. All rights reserved.

# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
# · Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
# · Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# · Neither the name of the EPRI nor the names of its contributors may be used
#   to endorse or promote products derived from this software without specific
#   prior written permission.

"""
Created on Fri Feb  4 13:07:24 2022

@author: pwre002
"""
import numpy as np


class VR_Model(object):
    """
    This is the voltage regulator (VR) control model, this model is used for dynamic simulation, to simulate the VR
    tap change performance external to the power flow solution engine.
    """

    def __init__(self,
                 name,              # Name of the voltage regulator
                 Ts,                # simulation time step (s)
                 Td_ctrl=30,        # delay time for control (s)
                 Td_tap=2,          # delay time for tapping (s)
                 Vref=120,          # reference voltage in 120V base (V)
                 db=2,              # deadband in 120V base (V)
                 LDC_R=0,           # Line Drop Compensation R
                 LDC_X=0,           # Line Drop Compensation X
                 PT_Ratio=120,      # PT ratio (Vpri/Vsec)
                 CT_Primary=100,    # CT primary rating (A)
                 tap_max=16,        # maximum tap position
                 tap_min=-16,       # minimum tap position
                 tap_ini=0,         # initial tap position
                 ):
        """
        Initialize the voltage regulator object model
        """
        self.name = name
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
        self.Vreg = 0

    def run(self,
            Vreg=None,  # regulating voltage  (magnitude on 120V base)
            Vpri=[],    # primary voltage (complex number in V)
            Ipri=[],    # primary current (complex number in A)
            ):
        """
        Determine voltage regulator tap position. If Vreg is not provided, Vreg will
        be calculated based on Vpri and Ipri and line drop compensation parameters.
        """

        # input conditioning
        if Vreg is None:
            Vsec = [x / self.PT_Ratio for x in Vpri]
            if Ipri != []:
                Vldc = [x / self.CT_Primary * (self.LDC_R + 1j * self.LDC_X) for x in Ipri]
            else:
                Vldc = [0 for x in Vpri]
            Vreg = np.mean(np.abs(np.array(Vsec) - np.array(Vldc)))

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



