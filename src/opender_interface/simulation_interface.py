from abc import ABC, abstractmethod

class SimulationInterfacesABC(ABC):


    @abstractmethod
    def initialize(self):
        pass

    @abstractmethod
    def load_scaling(self,mult=1.0):
        pass

    @abstractmethod
    def solve_power_flow(self):
        pass

    @abstractmethod
    def read_der_voltage(self):
        pass

    @abstractmethod
    def read_der_voltage_angle(self):
        pass

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
    def create_opender_objs(self, p_dc_pu = 1, DER_sim_type = None, **kwargs):
        pass

    @abstractmethod
    def enable_control(self):
        pass

    @abstractmethod
    def disable_control(self):
        pass

    @abstractmethod
    def read_vr(self):
        pass

    @abstractmethod
    def update_vr_tap(self):
        pass

    @abstractmethod
    def write_vr(self):
        pass

    @abstractmethod
    def create_vr_objs(self,vr_list):
        pass