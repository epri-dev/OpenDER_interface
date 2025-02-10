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

import pandas as pd
from opender import DER, DER_PV, DER_BESS, DERCommonFileFormat, DERCommonFileFormatBESS
from typing import Union, Tuple, List, Dict
from copy import deepcopy
from opender_interface.voltage_regulator import VR_Model
from opender_interface.dx_tool_interface import DxToolInterfacesABC
from opender_interface.opendss_interface import OpenDSSInterface
import os


class DERInterface:
    """
    This is the interface bridging OpenDER and distribution simulation tools for circuit level simulation.
    """

    # Converge criteria of V,P,Q
    V_TOLERANCE = 0.000001
    Q_TOLERANCE = 0.00001
    P_TOLERANCE = 0.01

    def __init__(self, simulator_ckt, t_s=DER.t_s, print_der=True):
        """
        Create the "DERInterface" object, assigning the provided simulator interface object to the "ckt" attribute.

        Input parameters:

        :param simulator_ckt: simulation tool interface object or simulation circuit file
        :param t_s: simulation time step
        :param print_der: If True, print_der OpenDER operation status whenever executed
        """

        if isinstance(simulator_ckt, DxToolInterfacesABC):
            self.ckt: DxToolInterfacesABC = simulator_ckt
        elif os.path.isfile(simulator_ckt):
            self.ckt: OpenDSSInterface = OpenDSSInterface(simulator_ckt)
        else:
            raise ValueError(f'Circuit simulation file path incorrect: {simulator_ckt}')

        self.der_objs = []
        self.t_s = t_s
        DER.t_s = t_s
        self.vr_objs = []

        self.__der_objs_temp = []

        # P and Q steps for each convergence iteration
        self.__delta_q = 0.2
        self.__delta_p = 0.5
        self.__numberofders = 0
        self.__der_files = []
        self.__der_bus = []

        self.__converged = False
        self.__v_converged = []
        self.__q_converged = []
        self.__p_converged = []

        self.__p_out = []
        self.__q_out = []

        self.__p_inv = []
        self.__q_inv = []

        self.__p_previous = []
        self.__q_previous = []

        self.__current_v = []
        self.__previous_v = []

        self.__p_check = []
        self.__q_check = []

        self.print_der = print_der

    def cmd(self, cmd_line: Union[str, List[str]]) -> Union[str, List[str]]:
        """
        Execute commands

        :param cmd_line: OpenDSS COM command in string or in list of strings
        """
        return self.ckt.cmd(cmd_line)

    def initialize(self, **kwargs):
        """
        Initialize and obtain circuit information. For OpenDSS simulation, please use the variable of DER_sim_type
        to provide the type of PC element which represents DERs (generator, PVSystem, isource, or vsource)

        :param DER_sim_type: Circuit element which represents DERs
        """

        self.ckt.initialize(**kwargs)

    def create_opender_objs(self, der_files: Union[Dict[str, DERCommonFileFormat], DERCommonFileFormat], p_pu=0) -> Union[List[DER_PV],List[DER_BESS]]:
        """
        Create OpenDER object on the circuit based on the DER configuration files provided. If a single
        DERCommonFileFormat object is provided, it is assumed all DERs on the circuit have the same ratings and control
        settings. If a dictionary is provided, please use the format of {'DER_name':DERCommonFileFormat}. DER_name
        should match the ones in the circuit definition. The created OpenDER objects will be returned as a list.

        Input parameters:

        :param der_files: Either a single DERCommonFileFormat object or a dictionary of them, containing the OpenDER
                          ratings and control settings.
        :param p_pu: initializing DER available power for PV or demanded active power for BESS. Default value is 0
        """

        # If received a single configuration file, convert to a dictionary
        if isinstance(der_files, DERCommonFileFormat) or isinstance(der_files, DERCommonFileFormatBESS):
            der_files = {der_obj[1]['name']: der_files for der_obj in self.ckt.DERs.iterrows()}

        for (index, der_i), setting in zip(self.ckt.DERs.iterrows(), der_files):
            created = False
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
                    created = True
            if not created:
                raise ValueError(f'DER named {der_i["name"]} does not have a configuration file specified')

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

        return self.der_objs

    def update_der_output_powers(self, der_list: List = None, p_list: List = None, q_list: List = None) -> None:
        """
        Update DER output information in terms of active and reactive power into the circuit simulation solver.
        p_list and q_list are used to specify P and Q values other than what are calculated in the OpenDER objects.
        Currently, this does not support DER as current source or voltage source behind impedance.

        :param der_list: Default is to update all DERs. If specified, only update part of the OpenDER objects.
        :param p_list: List of DER active power output in kW
        :param q_list: List of DER active power output in kvar
        """
        if der_list is None:
            der_list = self.der_objs

        self.ckt.update_der_output_powers(der_list, p_list, q_list)

    def set_source_voltage(self, v_pu: float) -> None:
        """
        Set circuit substation bus voltage

        :param v_pu: Substation bus voltage in pu
        """
        self.ckt.set_source_voltage(v_pu)

    def read_sys_voltage(self) -> pd.DataFrame:
        """
        Read and return bus voltages, obtained from circuit simulators
        :return: bus voltages in DataFrame, indexed by bus names. Also accessed by .ckt.buses
        """
        return self.ckt.read_sys_voltage()

    def read_der_voltage(self) -> Tuple[List, List]:
        """
        Return DER bus voltages and phase angles, obtained from circuit simulators. This is mostly used in
        self.run() method to execute the OpenDER calculation.
        :return: bus voltage (in pu) and angle (in radian) information for a DER
        """
        v_der_list = self.ckt.read_der_voltage()
        theta_der_list = self.ckt.read_der_voltage_angle()
        return v_der_list,theta_der_list

    def read_line_flow(self) -> pd.DataFrame:
        """
        Read and return power flow on all lines, obtained from circuit simulators
        :return: power flow information in DataFrame, indexed by line names. Also accessed by .ckt.lines
        """
        return self.ckt.read_line_flow()

    def solve_power_flow(self):
        """
        Solve circuit power flow using simulator engine
        """
        self.ckt.solve_power_flow()

    def create_vr_objs(self):
        """
        Create voltage regulator (VR_Model) object based on their definition in the circuit simulation tool
        """
        for fdr_vrname in self.ckt.VRs.keys():
            self.vr_objs.append(VR_Model(
                name=fdr_vrname,
                Ts=self.t_s,
                Td_ctrl=self.ckt.VRs[fdr_vrname]['delay'],
                Td_tap=self.ckt.VRs[fdr_vrname]['tapdelay'],
                Vref=self.ckt.VRs[fdr_vrname]['Vref'],
                db=self.ckt.VRs[fdr_vrname]['db'],
                LDC_R=self.ckt.VRs[fdr_vrname]['LDC_R'],
                LDC_X=self.ckt.VRs[fdr_vrname]['LDC_X'],
                PT_Ratio=self.ckt.VRs[fdr_vrname]['PT_Ratio'],
                CT_Primary=self.ckt.VRs[fdr_vrname]['CT_Primary'],
                tap_ini=0,
                ))

    def enable_control(self) -> None:
        """
        Enable voltage regulator controls in circuit simulation tool solver. This is usually for steady-state analysis
        or establish the initial condition for a dynamic simulation.
        """
        self.ckt.enable_control()

    def disable_control(self) -> None:
        """
        Disable voltage regulator controls in circuit simulation tool solver. This is usually for dynamic simulation
        """
        self.ckt.disable_control()

    def load_scaling(self, mult) -> None:
        """
        Scaling all loads in the circuit simulation tool

        :param mult: Multiplication factor
        """
        self.ckt.load_scaling(mult)

    def read_vr(self) -> None:
        """
        Read VR tap information from circuit.
        """
        self.ckt.read_vr()

    def write_vr(self):
        """
        Write voltage regulator tap information into circuit simulation, refer to specific simulator interface for details
        """
        for vr in self.vr_objs:
            self.ckt.VRs[vr.name]['tapPos'] = vr.tap
        self.ckt.write_vr()

    def update_vr_tap(self):
        """
        update voltage regulator tap position from circuit into VR model objects. Typically used after establishing
        the initial condition for a dynamic simulation.
        """
        for vr in self.vr_objs:
            vr.tap = float(self.ckt.VRs[vr.name]['tapPos'])

    def read_vr_v_i(self,vrname) -> Tuple[float, float]:
        """
        Return VR voltage and current derived from circuit simulator

        :param vrname: specify the VR name of which the voltage and current are needed
        """
        return self.ckt.read_vr_v_i(vrname)

    def run(self, der_objs=None):
        """
        Run OpenDER objects, utilizing circuit information such as DER bus voltages as input, and compute DER output.

        :param der_objs: By default, calculate all DER objects. If provided, this function will exclusively run
                        for the designated DER
        """

        if der_objs is None:
            der_objs = self.der_objs

        # Read DER terminal voltages
        self.read_sys_voltage()
        v_der_list, theta_der_list = self.read_der_voltage()
        for der, V, theta in zip(der_objs, v_der_list, theta_der_list):
            # Update the voltages to OpenDER objects, and Compute DER output power
            der.update_der_input(v_pu=list(V), theta=list(theta))
            der.run()
            # if self.print_der:
                # print(der, list(theta)[0], der.der_input.freq_hz)

        # run voltage regulator logics
        for vr in self.vr_objs:
            # read voltage regulator primary voltage
            Vpri, Ipri = self.read_vr_v_i(vr.name)
            # Voltage regulator operations
            vr.run(Vpri=Vpri, Ipri=Ipri)

    def __check_q(self):
        """
        Part of convergence process, identify DERs with volt-var or watt-var mode enabled. The reactive power output of
        these DERs will change a certain percentage between each convergence iteration.
        """
        for i in range(self.__numberofders):
            if self.__der_files[i].QP_MODE_ENABLE or self.__der_files[i].QV_MODE_ENABLE:
                self.__q_check[i] = True

    def __check_p(self):
        """
        Part of convergence process, identify DERs with volt-watt mode enabled. The active power output of
        these DERs will change a certain percentage between each convergence iteration.
        """
        for i in range(self.__numberofders):
            if self.__der_files[i].PV_MODE_ENABLE:
                self.__p_check[i] = True

    def __initialize_convergence(self):
        """
        Initialize the convergence process.
        """
        self.__cl_first_iteration = True
        self.__reset_converged()

        self.__p_check = [False for der_obj in self.der_objs]
        self.__q_check = [False for der_obj in self.der_objs]
        self.__check_p()
        self.__check_q()

    def __convergence_iteration(self):
        """
        Iteration for convergence process. Repeat the interation until the active power, reactive power, and terminal
        voltage of all the DERs in the circuit keep the same values. Convergence is reached at this point.
        """
        self.__reset_converged()

        self.__p_inv = [der_obj.p_out_kw for der_obj in self.__der_objs_temp]
        self.__q_inv = [der_obj.q_out_kvar for der_obj in self.__der_objs_temp]
        self.__current_v = [der_obj.der_input.v_meas_pu for der_obj in self.__der_objs_temp]

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
        """
        Reset convergence checkers, when initializing and each convergence iteration
        """
        self.__converged = False
        self.__v_converged = [False for der_obj in self.der_objs]
        self.__q_converged = [False for der_obj in self.der_objs]
        self.__p_converged = [False for der_obj in self.der_objs]

    def __check_v_criteria(self):
        """
        Check if the DER terminal voltages keep the same values between convergence iterations.
        """
        for i in range(self.__numberofders):
            if abs(self.__current_v[i] - self.__previous_v[i]) <= self.__class__.V_TOLERANCE:
                self.__v_converged[i] = True

    def __check_q_criteria(self):
        """
        Check if the DER output reactive powers keep the same values between convergence iterations.
        """
        for i in range(self.__numberofders):
            if abs(self.__q_out[i] - self.__q_inv[i]) <= self.__class__.Q_TOLERANCE:
                self.__q_converged[i] = True

    def __check_p_criteria(self):
        """
        Check if the DER output active powers keep the same values between convergence iterations.
        """
        for i in range(self.__numberofders):
            if abs(self.__p_out[i] - self.__p_inv[i]) <= self.__class__.P_TOLERANCE:
                self.__p_converged[i] = True

    def __check_converged(self):
        """
        Check if the DER terminal voltage, reactive and active powers keep the same values between convergence
        iterations.
        """
        self.__check_v_criteria()
        self.__check_p_criteria()
        self.__check_q_criteria()
        if all(self.__v_converged) and all(self.__q_converged) and all(self.__p_converged):
            self.__converged = True

    def __calculate_q_out(self):
        """
        For each iteration of convergence process, change only a certain percentage of DER output reactive power.
        """
        if self.__q_check:
            self.__q_out = [(q_inv - q_previous)*self.__delta_q+q_previous
                            for q_inv, q_previous in zip(self.__q_inv,self.__q_previous)]
        else:
            self.__q_out = self.__q_inv

    def __calculate_p_out(self):
        """
        For each iteration of convergence process, change only a certain percentage of DER output active power.
        """
        if self.__p_check:
            self.__p_out = [(p_inv - p_previous)*self.__delta_p+p_previous
                            for p_inv, p_previous in zip(self.__p_inv,self.__p_previous)]
        else:
            self.__q_out = self.__q_inv

    def der_convergence_process(self):
        """
        Convergence process. This is done by repetitively running power flow solutions and updating OpenDER outputs,
        until the convergence criteria for P, Q, V are met.
        """
        i = 0
        self.__initialize_convergence()

        while not self.__converged and i < 300:
            # Copy temporary OpenDER objects so any calculation does not impact their time responses.
            self.__der_objs_temp = deepcopy(self.der_objs)

            # Run the temporary OpenDER objects and update the outputs to circuit simulation
            self.run(self.__der_objs_temp)
            self.__convergence_iteration()
            self.update_der_output_powers(self.__der_objs_temp, self.__p_out, self.__q_out)
            self.solve_power_flow()
            i = i+1

        # After iteration, the simulation should be converged. Run the actual DER objects and solve power flow.
        self.run()
        self.update_der_output_powers()
        self.solve_power_flow()

        if self.__converged:
            return self.__p_out, self.__q_out
        else:
            print('convergence error!')

    def update_der_p_pu(self, p_pu_list):
        """
        Update active powers in per unit to OpenDER objects

        :param p_pu_list: List of active power (available DC power for PV or active power demand for BESS)  in per unit
        """
        for der, p_pu in zip(self.der_objs, p_pu_list):
            if isinstance(der, DER_BESS):
                der.update_der_input(p_dem_pu=p_pu, f=60)
            else:
                der.update_der_input(p_dc_pu=p_pu, f=60)

