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

    '''
    Used for record voltage regulator (VR) information
    '''
    @property
    @abstractmethod
    def VRs(self):
        pass

    # ******************************************************************************************************************
    # class method
    # ******************************************************************************************************************

    '''
    Initializing circuit 
    '''
    @abstractmethod
    def initialize(self,t_s,DER_sim_type,):
        pass

    '''
    Compile commands from user
    '''
    @abstractmethod
    def cmd(self,command):
        pass

    '''
    Update DER nameplate information to circuit
    '''
    @abstractmethod
    def update_der_info(self, name, der_obj):
        pass

    '''
    Scaling Load, input parameter "mult" refers to scaling factor.
    '''
    @abstractmethod
    def load_scaling(self,mult=1.0):
        pass

    '''
    Solve circuit power flow
    '''
    @abstractmethod
    def solve_power_flow(self):
        pass

    '''
    Read DER bus voltage magnitude
    '''
    @abstractmethod
    def read_der_voltage(self):
        pass

    '''
    Read line flow
    '''
    @abstractmethod
    def read_line_flow(self):
        pass

    '''
    Read DER bus voltage phase angle
    '''
    @abstractmethod
    def read_der_voltage_angle(self):
        pass

    '''
    Update DER output information (P, Q, I, V) into circuit
    '''
    @abstractmethod
    def update_der_output_powers(self, der_list, p_list=None, q_list=None):
        pass

    '''
    Set substation bus voltage
    '''
    @abstractmethod
    def set_source_voltage(self, v_pu):
        pass

    '''
    Read circuit bus voltages
    '''
    @abstractmethod
    def read_sys_voltage(self):
        pass

    @abstractmethod
    def enable_control(self):
        pass

    @abstractmethod
    def disable_control(self):
        pass

    '''
    Read VR tap information from circuit into "vtStates"
    '''
    @abstractmethod
    def read_vr(self):
        pass

    '''
    Write tap information from "vtStates" into circuit
    '''
    @abstractmethod
    def write_vr(self):
        pass

    '''
    Read the voltage and current of VR from circuit
    '''
    @abstractmethod
    def read_vr_v_i(self,vr):
        pass



