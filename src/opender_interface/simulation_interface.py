from abc import ABC, abstractmethod

class SimulationInterfacesABC(ABC):

    ## member

    ## has to be DataFrame
    @property
    @abstractmethod
    def DERs(self):
        pass

    @property
    @abstractmethod
    def vrStates(self):
        pass

    ## method

    ## initialize circuit, DERs and VRs
    @abstractmethod
    def initialize(self,t_s,DER_sim_type,):
        pass

    ## compile commands from user
    @abstractmethod
    def cmd(self,command):
        pass

    ## update DER nameplate info to circuit
    @abstractmethod
    def update_der_info(self, name, der_obj):
        pass

    @abstractmethod
    def load_scaling(self,mult=1.0):
        pass

    @abstractmethod
    def solve_power_flow(self):
        pass

    ## read DER bus voltage magnitute
    @abstractmethod
    def read_der_voltage(self):
        pass

    @abstractmethod
    def read_line_flow(self):
        pass

    ## read DER bus voltage phase angle
    @abstractmethod
    def read_der_voltage_angle(self):
        pass

    ## update DER output power into circuit
    @abstractmethod
    def update_der_output_powers(self, der_list, p_list=None, q_list=None):
        pass

    @abstractmethod
    def set_source_voltage(self, v_pu):
        pass

    @abstractmethod
    def read_sys_voltage(self):
        pass

    @abstractmethod
    def enable_control(self):
        pass

    @abstractmethod
    def disable_control(self):
        pass

    ## read vr tap from circuit into vrStates
    @abstractmethod
    def read_vr(self):
        pass

    ## Write vr_obj tap into circuit
    @abstractmethod
    def write_vr(self):
        pass

    ## read V/I of vr from circuit
    @abstractmethod
    def read_vr_v_i(self,vr):
        pass

    # @abstractmethod
    # def create_vr_objs(self,vr_list):
    #     pass

