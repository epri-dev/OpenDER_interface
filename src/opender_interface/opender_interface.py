from opender import DER, DER_PV, DER_BESS, DERCommonFileFormat, DERCommonFileFormatBESS
from typing import Union, Tuple, List, Dict
from copy import deepcopy
from opender_interface.voltage_regulator import VR_Model


class OpenDERInterface:

    '''
    This is the interface bridging OpenDER and multiple circuit simulators, as well as the interface connecting voltage
    regulator (VR: class of VR_Model) and circuit simulators.
    '''

    '''
    converge criteria of V,P,Q
    '''
    V_TOLERANCE = 0.000001
    Q_TOLERANCE = 0.00001
    P_TOLERANCE = 0.01

    '''
    Create an OpenDERInterface object, include simulator interface object (ckt), OpenDER object (der_objs) and VR object (vr_objs)
    Input parameters:
        simulator_ckt: simulator interface object, in current version, it is OpenDSSInterface object
        t_s: simulation time step, used for initialize OpenDER 
    '''
    def __init__(self, simulator_ckt, t_s=DER.t_s):
        self.ckt = simulator_ckt

        self.der_objs = []
        self.t_s = t_s
        DER.t_s = t_s
        self.vr_objs = {}

        self.__der_objs_temp = []

        self.__delta_q = 0.5
        self.__delta_p = 0.5

    '''
    Compile command from users in circuit simulators
    '''
    def cmd(self,command):
        self.ckt.cmd(command)

    '''
    Initialize circuit simulator object
    '''
    def initialize(self, DER_sim_type='PVSystem'):
        self.ckt.initialize(self.t_s,DER_sim_type)

    '''
    Create OpenDER object, update DER nameplate information
    Input parameters:
        der_files: DERCommonFileFormat or its inheritance classes, containing DER nameplate information
        p_pu: DER DC link available power, used for update DER input, default value is 0
    '''
    def create_opender_objs(self, der_files, p_pu=0):

        if isinstance(der_files, DERCommonFileFormat) or isinstance(der_files, DERCommonFileFormatBESS):
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


        self.__numberofders = len(self.der_objs)

        self.__der_files = [der_obj.der_file for der_obj in self.der_objs]
        self.__der_bus = [der_obj.bus for der_obj in self.der_objs]

        self.__converged = False
        self.__v_converged = [False for der_obj in self.der_objs]
        self.__q_converged = [False for der_obj in self.der_objs]
        self.__p_converged = [False for der_obj in self.der_objs]

        self.__p_out = [0 for der_obj in self.der_objs]
        self.__q_out = [0 for der_obj in self.der_objs]

        self.__p_inv = [0 for der_obj in self.der_objs]
        self.__q_inv = [0 for der_obj in self.der_objs]

        self.__p_previous = [0 for der_obj in self.der_objs]
        self.__q_previous = [0 for der_obj in self.der_objs]

        self.__current_v = [0 for der_obj in self.der_objs]
        self.__previous_v = [0 for der_obj in self.der_objs]

        self.__p_check = [False for der_obj in self.der_objs]
        self.__q_check = [False for der_obj in self.der_objs]

        # self.__cl_iteration = None

        return self.der_objs

    '''
    Update DER output into circuit 
    '''
    def update_der_output_powers(self, der_list=None, p_list=None, q_list=None):

        if der_list is None:
            der_list = self.der_objs

        self.ckt.update_der_output_powers(der_list,p_list,q_list)

    '''
    Set circuit substation voltage
    '''
    def set_source_voltage(self, v_pu: float):
        self.ckt.set_source_voltage(v_pu)

    '''
    Return bus voltages derived from circuit simulators
    '''
    def read_sys_voltage(self):
        return self.ckt.read_sys_voltage()

    '''
    Return DER bus voltages and phase angles derived from circuit simulators
    '''
    def read_der_voltage(self):
        v_der_list =  self.ckt.read_der_voltage()
        theta_der_list = self.ckt.read_der_voltage_angle()
        return v_der_list,theta_der_list

    '''
    Return line flow and current derived from circuit simulators
    '''
    def read_line_flow(self):
        return self.ckt.read_line_flow()

    '''
    Solve circuit power flow
    '''
    def solve_power_flow(self):
        self.ckt.solve_power_flow()

    '''
    Create VR_Model object, update VR information
    Input parameters:
        vr_list: list of vr information, containing name, tap information and so on, see example for details.
    '''
    def create_vr_objs(self, vr_list):
        # self.ckt.create_vr_objs(vr_list)
        for vr in vr_list:
            for fdr_vrname in self.ckt.vrStates.keys():
                if fdr_vrname == vr['name']:
                    self.vr_objs[fdr_vrname] = VR_Model(
                        Ts=100000,
                        # Ts=self.t_s,
                        Td_ctrl=vr['Td_ctrl'],
                        Td_tap=vr['Td_tap'],
                        Vref=self.ckt.vrStates[fdr_vrname]['Vref'],
                        db=self.ckt.vrStates[fdr_vrname]['db'],
                        LDC_R=self.ckt.vrStates[fdr_vrname]['LDC_R'],
                        LDC_X=self.ckt.vrStates[fdr_vrname]['LDC_X'],
                        PT_Ratio=self.ckt.vrStates[fdr_vrname]['PT_Ratio'],
                        CT_Primary=self.ckt.vrStates[fdr_vrname]['CT_Primary'],
                        tap_ini=0,
                        )

    def enable_control(self):
        self.ckt.enable_control()

    def load_scaling(self, mult):
        self.ckt.load_scaling(mult)

    '''
    Read VR tap from circuit
    '''
    def read_vr(self):
        self.ckt.read_vr()

    '''
    Write VR tap from VR object into circuit
    '''
    def write_vr(self):
        for vrname in self.vr_objs.keys():
            self.ckt.vrStates[vrname]['UpdatedTap']=self.vr_objs[vrname].tap
        self.ckt.write_vr()

    '''
    update VR tap from circuit into VR objects
    '''
    def update_vr_tap(self):
        for vrname in self.vr_objs.keys():
            self.vr_objs[vrname].tap = float(self.ckt.vrStates[vrname]['tapPos'])

    '''
    Return VR voltage and current derived from circuit simulator
    Input parameters:
        vrname: specify the VR name of which the voltage and current are needed
    '''
    def read_vr_v_i(self,vrname):
        return self.ckt.read_vr_v_i(vrname)

    def disable_control(self):
        self.ckt.disable_control()

    '''
    This is the function to run OpenDER object
    Input parameters:
        der_objs: if given, this function will only run specified DER object, otherwise the function will run all the 
        DER objects initialized in this class object 
    '''
    def run(self, der_objs=None):

        if der_objs is None:
            der_objs = self.der_objs

        self.read_sys_voltage()
        v_der_list, theta_der_list = self.read_der_voltage()
        for der, V, theta in zip(der_objs, v_der_list, theta_der_list):
            der.update_der_input(v_pu=V, theta=theta)
            der.run()
            print(der)


    def __check_q(self):
        for i in range(self.__numberofders):
            if self.__der_files[i].QP_MODE_ENABLE or self.__der_files[i].QV_MODE_ENABLE:
                self.__q_check[i] = True

    def __check_p(self):
        for i in range(self.__numberofders):
            if self.__der_files[i].PV_MODE_ENABLE:
                self.__p_check[i] = True

    def __initialize_time_step(self):
        self.__cl_first_iteration = True
        self.__reset_converged()

        self.__p_check = [False for der_obj in self.der_objs]
        self.__q_check = [False for der_obj in self.der_objs]
        self.__check_p()
        self.__check_q()

    def __control_loop_iteration(self):
        self.__reset_converged()

        self.__p_inv = [der_obj.p_out_kw for der_obj in self.__der_objs_temp]
        self.__q_inv = [der_obj.q_out_kvar for der_obj in self.__der_objs_temp]
        self.__current_v = [der_obj.der_input.v_meas_pu for der_obj in self.__der_objs_temp] #TODO update to threephase?

        if not self.__cl_first_iteration:
            self.__calculate_p_out()
            self.__calculate_q_out()
            self.__check_converged()
            self.__previous_v = self.__current_v
            self.__p_previous = self.__p_out
            self.__q_previous = self.__q_out
        else:
            self.__cl_first_iteration = False
            self.__previous_v = self.__current_v
            self.__p_previous = self.__p_inv
            self.__q_previous = self.__q_inv

            self.__p_out = self.__p_inv
            self.__q_out = self.__q_inv

    def __reset_converged(self):
        self.__converged = False
        self.__v_converged = [False for der_obj in self.der_objs]
        self.__q_converged = [False for der_obj in self.der_objs]
        self.__p_converged = [False for der_obj in self.der_objs]

    def __check_v_criteria(self):
        for i in range(self.__numberofders):
            if abs(self.__current_v[i] - self.__previous_v[i]) <= self.__class__.V_TOLERANCE:
                self.__v_converged[i] = True

    def __check_q_criteria(self):
        for i in range(self.__numberofders):
            if abs(self.__q_out[i] - self.__q_inv[i]) <= self.__class__.Q_TOLERANCE:
                self.__q_converged[i] = True
            # else:
                # print(self._q_out[i] - self._q_inv[i])

    def __check_p_criteria(self):
        for i in range(self.__numberofders):
            if abs(self.__p_out[i] - self.__p_inv[i]) <= self.__class__.P_TOLERANCE:
                self.__p_converged[i] = True

    def __check_converged(self):
        self.__check_v_criteria()
        self.__check_p_criteria()
        self.__check_q_criteria()
        if all(self.__v_converged) and all(self.__q_converged) and all(self.__p_converged):
            self.__converged = True

    def __calculate_q_out(self):
        # if self._q_check:
        #     self._q_out = (self._q_inv - self._q_previous) * self._delta_q + self._q_previous
        # else:
        #     self._q_out = self._q_inv

        if self.__q_check:
            self.__q_out = [(q_inv - q_previous)*self.__delta_q+q_previous
                           for q_inv, q_previous in zip(self.__q_inv,self.__q_previous)]
        else:
            self.__q_out = self.__q_inv

    def __calculate_p_out(self):
        # if self._p_check:
        #     self._p_out = (self._p_inv - self._p_previous) * self._delta_p + self._p_previous
        # else:
        #     self._p_out = self._p_inv
        if self.__p_check:
            self.__p_out = [(p_inv - p_previous)*self.__delta_p+p_previous
                           for p_inv, p_previous in zip(self.__p_inv,self.__p_previous)]
        else:
            self.__q_out = self.__q_inv

    '''
    This is the function for running convergence process of DER. This function will run DER until P,Q,V reaches the 
    convergence criteria or finished 100 iterations.
    '''
    def der_convergence_process(self):
        # v_control_i_list = list()
        # q_control_i_list = list()
        i = 0
        self.__initialize_time_step()

        while not self.__converged and i < 100:
            self.__der_objs_temp = deepcopy(self.der_objs)
            self.run(self.__der_objs_temp)
            self.__control_loop_iteration()
            self.update_der_output_powers(self.__der_objs_temp, self.__p_out, self.__q_out)
            self.solve_power_flow()
            i = i+1

        self.run()
        self.update_der_output_powers()
        self.solve_power_flow()

        if self.__converged:
            return self.__p_out, self.__q_out
        else:
            print('convergence error!')


    '''
    This is the function used for update DER DC link power
    Input parameters:
        p_pu_list: users provided liast of DER DC link power
    '''
    def update_der_p_pu(self, p_pu_list):
        for der, p_pu in zip(self.der_objs, p_pu_list):
            if isinstance(der, DER_BESS):
                der.update_der_input(p_dem_pu=p_pu, f=60)
            else:
                der.update_der_input(p_dc_pu=p_pu, f=60)

