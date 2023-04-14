from opender import DER, DER_PV, DER_BESS, DERCommonFileFormat, DERCommonFileFormatBESS
from . import simulation_interface
from opender_interface.opendss_interface import OpenDSSInterface
from typing import Union, Tuple, List, Dict
from copy import deepcopy

class OpenDERInterface:

    v_tolerance = 0.000001
    q_tolerance = 0.00001
    p_tolerance = 0.01

    def __init__(self, ckt_path, t_s=DER.t_s):
        if '.dss' in str(ckt_path):
            self.ckt = OpenDSSInterface(ckt_path)
            self.dss = self.ckt.dss
        else:
            print('File path error!')

        self.der_objs = []
        self.t_s = t_s
        DER.t_s = t_s
        self.der_objs_temp = []

        self._delta_q = 0.5
        self._delta_p = 0.5


    def initialize(self, DER_sim_type='PVSystem'):
        self.ckt.initialize(DER_sim_type)
    def create_opender_objs(self, der_files, p_pu=0):

        if isinstance(der_files, Union[DERCommonFileFormat, DERCommonFileFormatBESS]):
            der_files= {der_obj[1]['name']: der_files for der_obj in self.ckt.DERs.iterrows()}


        for (index, der_i), setting in zip(self.ckt.DERs.iterrows(), der_files):
            for name, der_file in der_files.items():
                if name.upper() == der_i['name'].upper():
                    if 'PV' in der_i['name'].upper():
                        der_obj = DER_PV(der_file)
                    else:
                        if not isinstance(der_file, DERCommonFileFormatBESS):
                            der_file = DERCommonFileFormatBESS(convert=der_file)
                        der_obj = DER_BESS(der_file)

                    self.ckt.update_der_info(name, der_obj)

                    der_obj.name = der_i['name']
                    der_obj.bus = der_i['bus']
                    der_obj.der_file.NP_V_DC = der_i['kV'] * 1500
                    der_obj.der_file.NP_AC_V_NOM = der_i['kV'] * 1000

                    DER.t_s = self.t_s
                    if isinstance(der_obj, DER_BESS):
                        der_obj.update_der_input(p_dem_pu=p_pu, f=60)
                    else:
                        der_obj.update_der_input(p_dc_pu=p_pu, f=60)




                    self.der_objs.append(der_obj)


        self.numberofders = len(self.der_objs)

        self.der_files = [der_obj.der_file for der_obj in self.der_objs]
        self.der_bus = [der_obj.bus for der_obj in self.der_objs]

        self._converged = False
        self._v_converged = [False for der_obj in self.der_objs]
        self._q_converged = [False for der_obj in self.der_objs]
        self._p_converged = [False for der_obj in self.der_objs]

        self._p_out = [0 for der_obj in self.der_objs]
        self._q_out = [0 for der_obj in self.der_objs]

        self._p_inv = [0 for der_obj in self.der_objs]
        self._q_inv = [0 for der_obj in self.der_objs]

        self._p_previous = [0 for der_obj in self.der_objs]
        self._q_previous = [0 for der_obj in self.der_objs]

        self._current_v = [0 for der_obj in self.der_objs]
        self._previous_v = [0 for der_obj in self.der_objs]

        self._p_check = [False for der_obj in self.der_objs]
        self._q_check = [False for der_obj in self.der_objs]

        self._cl_iteration = None


        return self.der_objs


    def update_der_output_powers(self, der_list=None, p_list=None, q_list=None):

        if der_list is None:
            der_list = self.der_objs

        self.ckt.update_der_output_powers(der_list,p_list,q_list)
    def read_sys_voltage(self):
        return self.ckt.read_sys_voltage()

    def read_line_flow(self):
        return self.ckt.read_line_flow()
    def solve_power_flow(self):
        self.ckt.solve_power_flow()

    def create_vr_objs(self, vr_list):
        self.ckt.create_vr_objs(vr_list)

    def enable_control(self):
        self.ckt.enable_control()

    def load_scaling(self, mult):
        self.ckt.load_scaling(mult)

    def read_vr(self):
        self.ckt.read_vr()

    def write_vr(self):
        self.ckt.write_vr()
    def update_vr_tap(self):
        self.ckt.update_vr_tap()

    def disable_control(self):
        self.ckt.disable_control()


    def _check_q(self):
        for i in range(self.numberofders):
            if self.der_files[i].QP_MODE_ENABLE or self.der_files[i].QV_MODE_ENABLE:
                self._q_check[i] = True

    def _check_p(self):
        for i in range(self.numberofders):
            if self.der_files[i].PV_MODE_ENABLE:
                self._p_check[i] = True

    def initialize_time_step(self):
        self._cl_first_iteration = True
        self._reset_converged()

        self._p_check = [False for der_obj in self.der_objs]
        self._q_check = [False for der_obj in self.der_objs]
        self._check_p()
        self._check_q()


    def control_loop_iteration(self):
        self._reset_converged()

        self._p_inv = [der_obj.p_out_kw for der_obj in self.der_objs_temp]
        self._q_inv = [der_obj.q_out_kvar for der_obj in self.der_objs_temp]
        self._current_v = [der_obj.der_input.v_meas_pu for der_obj in self.der_objs_temp] #TODO update to threephase?

        if not self._cl_first_iteration:
            self._calculate_p_out()
            self._calculate_q_out()
            self._check_converged()
            self._previous_v = self._current_v
            self._p_previous = self._p_out
            self._q_previous = self._q_out
        else:
            self._cl_first_iteration = False
            self._previous_v = self._current_v
            self._p_previous = self._p_inv
            self._q_previous = self._q_inv

            self._p_out = self._p_inv
            self._q_out = self._q_inv

    def _reset_converged(self):
        self._converged = False
        self._v_converged = [False for der_obj in self.der_objs]
        self._q_converged = [False for der_obj in self.der_objs]
        self._p_converged = [False for der_obj in self.der_objs]

    def _check_v_criteria(self):
        for i in range(self.numberofders):
            if abs(self._current_v[i] - self._previous_v[i]) <= self.__class__.v_tolerance:
                self._v_converged[i] = True

    def _check_q_criteria(self):
        for i in range(self.numberofders):
            if abs(self._q_out[i] - self._q_inv[i]) <= self.__class__.q_tolerance:
                self._q_converged[i] = True
            # else:
                # print(self._q_out[i] - self._q_inv[i])

    def _check_p_criteria(self):
        for i in range(self.numberofders):
            if abs(self._p_out[i] - self._p_inv[i]) <= self.__class__.p_tolerance:
                self._p_converged[i] = True

    def _check_converged(self):
        self._check_v_criteria()
        self._check_p_criteria()
        self._check_q_criteria()
        if all(self._v_converged) and all(self._q_converged) and all(self._p_converged):
            self._converged = True

    def _calculate_q_out(self):
        # if self._q_check:
        #     self._q_out = (self._q_inv - self._q_previous) * self._delta_q + self._q_previous
        # else:
        #     self._q_out = self._q_inv

        if self._q_check:
            self._q_out = [(q_inv - q_previous)*self._delta_q+q_previous
                           for q_inv, q_previous in zip(self._q_inv,self._q_previous)]
        else:
            self._q_out = self._q_inv

    def _calculate_p_out(self):
        # if self._p_check:
        #     self._p_out = (self._p_inv - self._p_previous) * self._delta_p + self._p_previous
        # else:
        #     self._p_out = self._p_inv
        if self._p_check:
            self._p_out = [(p_inv - p_previous)*self._delta_p+p_previous
                           for p_inv, p_previous in zip(self._p_inv,self._p_previous)]
        else:
            self._q_out = self._q_inv

    def der_convergence_process(self):
        # v_control_i_list = list()
        # q_control_i_list = list()
        i = 0
        self.initialize_time_step()

        while not self._converged and i < 100:
            self.der_objs_temp = deepcopy(self.der_objs)
            self.run(self.der_objs_temp)
            self.control_loop_iteration()
            self.ckt.update_der_output_powers(self.der_objs_temp, self._p_out, self._q_out)
            self.ckt.solve_power_flow()

        self.run()
        self.update_der_output_powers()
        self.ckt.solve_power_flow()

        if self._converged:
            return self._p_out, self._q_out
        else:
            print('convergence error!')


    def run(self, der_objs=None):
        if der_objs is None:
            der_objs = self.der_objs

        self.ckt.read_sys_voltage()
        v_der_list = self.ckt.read_der_voltage()
        theta_der_list = self.ckt.read_der_voltage_angle()
        for der, V, theta in zip(der_objs, v_der_list, theta_der_list):
            der.update_der_input(v_pu=V, theta=theta)
            der.run()
            print(der)
    def update_der_p_pu(self, p_pu_list):
        for der, p_pu in zip(self.der_objs, p_pu_list):
            if isinstance(der, DER_BESS):
                der.update_der_input(p_dem_pu=p_pu, f=60)
            else:
                der.update_der_input(p_dc_pu=p_pu, f=60)


