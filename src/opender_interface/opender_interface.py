from opender import der
from . import simulation_interface
from typing import List

class DERModelInterface:

    v_tolerance = 0.000001
    q_tolerance = 0.00001
    p_tolerance = 0.01

    def __init__(self, ckt_interface, p_dc_pu, **kwargs):

        self.ckt_interface = ckt_interface
        self.der_objs = self._create_der_objs(p_dc_pu, **kwargs)

        self.numberofders = len(self.der_objs)

        self.der_files = [der_obj.der_file for der_obj in self.der_objs]
        self.der_bus = [der_obj.bus for der_obj in self.der_objs]

        self._converged = False
        self._v_converged = [False for der_obj in self.der_objs]
        self._q_converged = [False for der_obj in self.der_objs]
        self._p_converged = [False for der_obj in self.der_objs]

        self._p_out = [None for der_obj in self.der_objs]
        self._q_out = [None for der_obj in self.der_objs]

        self._p_inv = [None for der_obj in self.der_objs]
        self._q_inv = [None for der_obj in self.der_objs]

        self._p_previous = [None for der_obj in self.der_objs]
        self._q_previous = [None for der_obj in self.der_objs]

        self._current_v = [None for der_obj in self.der_objs]
        self._previous_v = [None for der_obj in self.der_objs]

        self._delta_p = [None for der_obj in self.der_objs]
        self._delta_q = [None for der_obj in self.der_objs]

        self._p_check = [False for der_obj in self.der_objs]
        self._q_check = [False for der_obj in self.der_objs]

        self._cl_iteration = None

    def _create_der_objs(self, p_dc_pu, **kwargs):
        der_list = []
        for index, der_i in self.ckt_interface.DERs.iterrows():
            der_obj = der.DER()
            der_obj.der_file.NP_VA_MAX = der_i['kVA'] * 1000
            der_obj.der_file.NP_P_MAX = der_i['kw'] * 1000
            der_obj.der_file.NP_Q_MAX_ABS = der_i['kvar'] * 1000
            der_obj.der_file.NP_Q_MAX_INJ = der_i['kvarabs'] * 1000
            der_obj.name = der_i['name']
            der_obj.bus = der_i['bus']
            der_obj.der_file.NP_V_DC = der_i['kV'] * 1500
            der_obj.der_file.NP_AC_V_NOM = der_i['kV'] * 1000

            der.DER.t_s = self.ckt_interface.tstep
            der_obj.update_der_input(p_dc_pu=p_dc_pu, f=60)
            try:
                for key, value in kwargs.items():
                    setattr(der_obj.der_file, key, value)
            except:
                print('ERROR applying DER settings!')

            # der_obj.reinitialize()

            # save the in the der_list(
            der_list.append(der_obj)
        return der_list
    
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

        self._delta_q = 0.5
        self._delta_p = 0.5

    def control_loop_iteration(self):
        self._reset_converged()

        self._p_inv = [der_obj.p_out_kw for der_obj in self.der_objs]
        self._q_inv = [der_obj.q_out_kvar for der_obj in self.der_objs]
        self._current_v = [der_obj.der_input.v_meas_pu for der_obj in self.der_objs] #TODO update to threephase?

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

        tmp_t_s = der.DER.t_s
        der.DER.t_s = 10000

        while not self._converged and i < 100:
            i += 1
            self.ckt_interface.solve_power_flow()
            self.ckt_interface.read_sys_voltage()
            self.ckt_interface.read_line_flow()

            v_list = self.ckt_interface.read_der_voltage(self.der_bus)
            theta_list = self.ckt_interface.read_der_voltage_angle(self.der_bus)
            for der_obj,v_pu,theta in zip(self.der_objs,v_list,theta_list):   # type: der.DER
                der_obj.update_der_input(v_pu=v_pu,theta=theta)

            for der_obj in self.der_objs:
                der_obj.run()
                print(der_obj)
                print(der_obj.ridethroughperf)

            self.control_loop_iteration()

            self.ckt_interface.update_der_output_powers(self.der_objs, self._p_out, self._q_out)

        self.ckt_interface.solve_power_flow()
        der.DER.t_s = tmp_t_s
        for der_obj in self.der_objs:
            der_obj.time = 0

        if self._converged:
            return self._p_out, self._q_out


    def run(self, p_dc_pu_list = None):
        v_der_list = self.ckt_interface.read_der_voltage()
        theta_der_list = self.ckt_interface.read_der_voltage_angle()
        if p_dc_pu_list is None:
            for der, V, theta in zip(self.der_objs, v_der_list, theta_der_list):
                der.update_der_input(v_pu=V, p_dc_pu=1, theta=theta)
                der.run()
                print(der)
        else:
            for der, V, theta, p_dc_pu in zip(self.der_objs, v_der_list, theta_der_list, p_dc_pu_list):
                der.update_der_input(v_pu=V, p_dc_pu=p_dc_pu, theta=theta)
                der.run()
                print(der)

    def solve_power_flow(self):
        self.ckt_interface.solve_power_flow()



der_interface = DERModelInterface(1,1,**{'a':1})
