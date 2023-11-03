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

from abc import ABC, abstractmethod


class DxToolInterfacesABC(ABC):
    """
    This abstract class serves as a template for the application program interface for the distribution analysis tools.
    """

    @property
    @abstractmethod
    def DERs(self):
        """
        OpenDER objects
        """
        pass

    @property
    @abstractmethod
    def VRs(self):
        """
        Used for record voltage regulator (VR) information
        """
        pass

    @abstractmethod
    def initialize(self,t_s,DER_sim_type,):
        """
        Initialize and obtain circuit information. please use the variable of DER_sim_type
        to provide the type of PC element which represents DERs (generator, PVSystem, isource, or vsource)

        :param DER_sim_type: Circuit element which represents DERs. The default type is "PVSystem".
        """

        pass

    @abstractmethod
    def update_der_info(self, name, der_obj):
        """
        Update DER nameplate information into circuit.

        :param name: name of the specific DER to be updated
        :param der_obj: DER object, an instance of the "OpenDER" class, containing DER nameplate information
        """
        pass


    @abstractmethod
    def load_scaling(self,mult=1.0):
        """
        Scaling all loads in the circuit simulation tool

        :param mult: Multiplication factor
        """
        pass

    @abstractmethod
    def solve_power_flow(self):
        """
        Solve circuit power flow using distribution analysis tool engine
        """
        pass

    @abstractmethod
    def read_der_voltage(self):
        """
        Return bus voltages for DERs, from circuit simulators

        :param der_bus_list: Default is all DER. If specified, only selected DERs
        :return: bus voltage magnitude information for a DER, in pu
        """
        pass

    @abstractmethod
    def read_line_flow(self):
        """
        Read and return power flow on all lines, obtained from circuit simulators

        :return: power flow information in DataFrame, indexed by line names. Also accessed by .lines
        """
        pass

    @abstractmethod
    def read_der_voltage_angle(self):
        """
        Return bus voltage angles for DERs, from circuit simulators

        :param der_bus_list: Default is all DER. If specified, only selected DERs
        :return: bus voltage angle information for a DER, in radian
        """
        pass


    @abstractmethod
    def update_der_output_powers(self, der_list, p_list=None, q_list=None):
        """
        Update DER output information in terms of active and reactive power into the circuit simulation solver.
        p_list and q_list are used to specify P and Q values other than what are calculated in the OpenDER objects.
        Currently, this does not support DER as current source or voltage source behind impedance.

        :param der_list: Default is to update all DERs. If specified, only update part of the OpenDER objects.
        :param p_list: List of DER active power output in kW
        :param q_list: List of DER active power output in kvar
        """
        pass

    @abstractmethod
    def set_source_voltage(self, v_pu):
        """
        Set circuit substation bus voltage
        """
        pass

    @abstractmethod
    def read_sys_voltage(self):
        """
        Read and return bus voltages derived from circuit simulators

        :return: bus voltages in DataFrame, indexed by bus names. Also accessed by .buses
        """
        pass

    @abstractmethod
    def enable_control(self):
        """
        Enable voltage regulator controls in OpenDSS. This is usually for steady-state analysis
        or establish the initial condition for a dynamic analysis.
        """
        pass

    @abstractmethod
    def disable_control(self):
        """
        Disable voltage regulator controls in circuit simulation tool solver. This is usually for dynamic simulation
        """
        pass

    @abstractmethod
    def read_vr(self):
        """
        Read voltage regulator tap information from OpenDSS circuit into the class
        """
        pass

    @abstractmethod
    def write_vr(self):
        """
        Write voltage regulator tap information from the class into OpenDSS circuit simulation.
        """
        pass

    @abstractmethod
    def read_vr_v_i(self,vr):
        """
        Return VR voltage and current information from OpenDSS circuit

        :param vrname: name of voltage regulator
        :return: Voltage and current
        """
        pass



