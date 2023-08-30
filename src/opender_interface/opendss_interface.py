import py_dss_interface
import numpy as np
import pandas as pd
import cmath
from typing import Union, List
from opender_interface.dx_tool_interface import DxToolInterfacesABC


class OpenDSSInterface(DxToolInterfacesABC):
    """
    This is the OpenDSS interface, which is an inheritance class of DxToolInterfacesABC
    """

    @property
    def DERs(self):
        """
        Used for record DER information
        """
        return self._DERs

    @property
    def VRs(self):
        """
        Used for record voltage regulator (VR) information
        """
        return self._VRs

    def __init__(self, dss_file: str) -> None:
        """
        To create an "OpenDSSInterface" object

        :param dss_file: the specific dss file to be compiled
        """

        self.dss_file = dss_file
        self.dss = py_dss_interface.DSS()
        self.der_bus_list = []

        self.dss.text(f"Compile [{self.dss_file}]")

        self._DERs = []
        self._VRs = {}
        self.DER_sim_type = None

    def cmd(self, cmd_line: Union[str, List[str]]) -> Union[str, List[str]]:
        """
        Compile dss command from user

        :param cmd_line: OpenDSS COM command in string or list of strings
        """

        if type(cmd_line) is list:
            return [self.dss.text(cmd) for cmd in cmd_line]
        elif type(cmd_line) is str:
            return self.dss.text(cmd_line)
        else:
            raise ValueError("OpenDSS Initializing cmd_list is not valid")

    def initialize(self, DER_sim_type='PVSystem', **kwargs):
        """
        Initialize and obtain circuit information. please use the variable of DER_sim_type
        to provide the type of PC element which represents DERs (generator, PVSystem, isource, or vsource)

        :param DER_sim_type: Circuit element which represents DERs. The default type is "PVSystem".
        """

        self.DER_sim_type = DER_sim_type.lower()
        if self.DER_sim_type not in ['pvsystem', 'generator', 'isource', 'vsource']:
            raise ValueError(
                f"DER_sim_type should be 'pvsystem', 'generator', 'isource', 'vsource'. Now it is {DER_sim_type}")

        self.__init_buses()
        self.__init_lines()
        self.__init_loads()
        self.__init_generators()
        self.__init_vr()

        if self.DER_sim_type == 'pvsystem':
            self.__init_PVSystems()
        if self.DER_sim_type == 'isource':
            self.__init_isources()
        if self.DER_sim_type == 'vsource':
            self.__init_vsources()
        if self.DER_sim_type == 'generator':
            self._DERs = self.generators
            self.der_bus_list = self.gen_bus_list

    def __init_buses(self):
        """
        Read the information of all the buses into this class, stored in self.buses
        """

        nodenames = list(self.dss.circuit.nodes_names)
        buses = []
        for busname in self.dss.circuit.buses_names:
            self.dss.circuit.set_active_bus(busname)
            try:
                idx_A = nodenames.index('{}.{}'.format(busname, 1))
            except ValueError:
                idx_A = -1
            try:
                idx_B = nodenames.index('{}.{}'.format(busname, 2))
            except ValueError:
                idx_B = -1
            try:
                idx_C = nodenames.index('{}.{}'.format(busname, 3))
            except ValueError:
                idx_C = -1
            buses.append({
                'name': busname,
                'kVBaseLL': self.dss.bus.kv_base * np.sqrt(3),
                'nPhases': self.dss.bus.num_nodes,
                'distance': self.dss.bus.distance * 0.621371,  # km to miles
                'x': self.dss.bus.x,
                'y': self.dss.bus.y,
                'nodeIndex_A': idx_A,
                'nodeIndex_B': idx_B,
                'nodeIndex_C': idx_C,
                'Vpu_A': 1.0,
                'Vpu_B': 1.0,
                'Vpu_C': 1.0,
                'Theta_A': 0,
                'Theta_B': -2.0943951,
                'Theta_C': 2.0943951
            })
        self.buses = pd.DataFrame(buses)
        self.buses.set_index('name', inplace=True)
        self.buses = self.buses.astype(dtype={
            'nPhases': 'int64',
            'nodeIndex_A': 'int64',
            'nodeIndex_B': 'int64',
            'nodeIndex_C': 'int64',
        })


    def __init_lines(self):
        """
        Read the information of all the lines into this class, stored in self.lines
        """
        linenames = list(self.dss.lines.names)
        lines = []
        for linename in linenames:
            self.dss.lines.name = linename
            bus1 = self.dss.lines.bus1.split('.')[0]
            bus2 = self.dss.lines.bus2.split('.')[0]
            self.dss.circuit.set_active_bus(bus1)
            lines.append({
                'name': linename,
                'bus1': bus1,
                'bus2': bus2,
                'kVBaseLN': self.dss.bus.kv_base,
                'nPhases': self.dss.lines.phases,
                'length': self.dss.lines.length,
                'normamps': self.dss.lines.norm_amps,
                'emergamps': self.dss.lines.emerg_amps,
                'flowI_A': 0 + 1j * 0,
                'flowI_B': 0 + 1j * 0,
                'flowI_C': 0 + 1j * 0,
                'flowS_A': 0 + 1j * 0,
                'flowS_B': 0 + 1j * 0,
                'flowS_C': 0 + 1j * 0,
            })
        self.lines = pd.DataFrame(lines)
        self.lines.set_index('name', inplace=True)
        self.lines = self.lines.astype(dtype={
            'nPhases': 'int64',
        })


    def __init_loads(self):
        """
        Read the information of all the loads into this class, stored in self.loads
        """

        loadnames = self.dss.loads.names
        if loadnames[0] == 'NONE':
            loadnames = []
        loads = []
        for loadname in loadnames:
            self.dss.loads.name = loadname
            kw = self.dss.loads.kw
            bus = self.dss.text(f'? load.{loadname}.bus1')
            phases = int(self.dss.text(f'? load.{loadname}.phases'))

            this_type = 'load'
            loads.append({
                'name': loadname,
                'type': this_type,
                'bus': bus.split('.')[0].replace(' ', ''),
                'nodes': bus,
                'phases': phases,
                'kw': kw,
            })
        self.loads = pd.DataFrame(loads)
        if not self.loads.empty:
            self.loads.set_index('name', inplace=True)


    def __init_generators(self):
        """
        Read the information of all the generators into this class, stored in self.generators
        """
        gennames = list(self.dss.generators.names)
        if gennames[0] == 'NONE':
            gennames = []
        self.gen_bus_list = []
        gens = []
        for genname in gennames:
            self.dss.generators.name = genname
            kw = self.dss.generators.kw
            kvar = self.dss.generators.kvar
            kVA = self.dss.generators.kva
            bus = self.dss.text(f'? generator.{genname}.bus1')
            kV = float(self.dss.text(f'? generator.{genname}.kv'))
            this_type = 'generator'
            gens.append({
                'name': genname,
                'type': this_type,
                'bus': bus.split('.')[0].replace(' ', ''),
                'kw': kw,
                'kvar': kvar,
                'kVA': kVA,
                'kV': kV,
            })
            self.gen_bus_list.append(bus.split('.')[0].replace(' ', ''))

        self.generators = pd.DataFrame(gens)

    def __init_PVSystems(self):
        """
        Read the information of all the PVSystems into this class, stored in self.DERs
        """
        PVnames = list(self.dss.pvsystems.names)
        if PVnames[0] == 'NONE':
            PVnames = []
        PVs = []
        for PVname in PVnames:
            self.dss.pvsystems.name = PVname
            kw = self.dss.pvsystems.pmpp
            kvar = self.dss.pvsystems.kvar
            kVA = self.dss.pvsystems.kva
            bus = self.dss.text(f'? PVSystem.{PVname}.bus1')
            kvarabs = float(self.dss.text(f'? PVSystem.{PVname}.kvarmaxabs'))
            kV = float(self.dss.text(f'? PVSystem.{PVname}.kv'))
            this_type = 'PVSystem'
            PVs.append({
                'name': PVname,
                'type': this_type,
                'bus': bus.split('.')[0].replace(' ', ''),
                'kw': kw,
                'kvar': kvar,
                'kvarabs': kvarabs,
                'kVA': kVA,
                'kV': kV
            })
            self.der_bus_list.append(bus.split('.')[0].replace(' ', ''))

        self._DERs = pd.DataFrame(PVs)

    def __init_isources(self):
        """
        Read the information of all the isources into this class, stored in self.DERs
        """
        PVnames = list(self.dss.isources.names)
        PVs = []
        PVnames = [PVname.split('_')[0].replace(' ', '') for PVname in PVnames]
        PVnames = [*set(PVnames)]
        for PVname in PVnames:
            self.dss.isources.name = f'{PVname}_a'
            bus = self.dss.text(f'? isource.{PVname}_a.bus1')
            self.dss.circuit.set_active_bus(bus)
            kV = self.dss.bus.kv_base * 1.7320508075688

            this_type = 'isource'
            PVs.append({
                'name': PVname,
                'type': this_type,
                'bus': bus.split('.')[0].replace(' ', ''),
                'kw': 100,
                'kvar': 44,
                'kvarabs': 44,
                'kVA': 100,
                'kV': kV
            })
            self.der_bus_list.append(bus.split('.')[0].replace(' ', ''))

        self._DERs = pd.DataFrame(PVs)

    def __init_vsources(self):
        """
        Read the information of all the vsources into this class, stored in self.DERs
        """
        PVnames = list(self.dss.vsources.names)[1:]  # First one is substation
        PVs = []
        PVnames = [PVname.split('_')[0].replace(' ', '') for PVname in PVnames]
        PVnames = [*set(PVnames)]
        for PVname in PVnames:
            self.dss.vsources.name = f'{PVname}_a'
            kw = float(self.dss.text(f'? vsource.{PVname}_a.baseMVA')) * 1000
            kVA = float(self.dss.text(f'? vsource.{PVname}_a.baseMVA')) * 1000
            bus = self.dss.text(f'? vsource.{PVname}_a.bus1')
            self.dss.circuit.set_active_bus(bus)
            kV = self.dss.bus.kv_base * 1.7320508075688

            this_type = 'vsource'
            PVs.append({
                'name': PVname,
                'type': this_type,
                'bus': bus.split('.')[0].replace(' ', ''),
                'kw': kw,
                'kvar': kw,
                'kvarabs': kw,
                'kVA': kVA,
                'kV': kV
            })
            self.der_bus_list.append(bus.split('.')[0].replace(' ', ''))

        self._DERs = pd.DataFrame(PVs)

    def update_der_info(self, name, der_obj):
        """
        Update DER nameplate information into dss circuit.

        :param name: name of the specific DER to be updated
        :param der_obj: DER object, an instance of the "OpenDER" class, containing DER nameplate information
        """

        if self.DER_sim_type == 'pvsystem':
            self.dss.text(f'PVSystem.{name}.kVA = {der_obj.der_file.NP_VA_MAX / 1000}')
            self.dss.text(f'PVSystem.{name}.Pmpp = {der_obj.der_file.NP_P_MAX / 1000}')
            self.dss.text(f'PVSystem.{name}.kvarmax = {der_obj.der_file.NP_Q_MAX_ABS / 1000}')
            self.dss.text(f'PVSystem.{name}.kvarmaxabs = {der_obj.der_file.NP_Q_MAX_INJ / 1000}')

        if self.DER_sim_type == 'isource':
            pass

        if self.DER_sim_type == 'vsource':
            self.dss.vsources.name = f'{name}_a'
            kVA = der_obj.der_file.NP_VA_MAX / 1000
            bus = self.dss.text(f'? vsource.{name}_a.bus1')
            self.dss.circuit.set_active_bus(bus)

            kV = self.dss.bus.kv_base * 1.7320508075688
            R = der_obj.der_file.NP_RESISTANCE * kV * kV / kVA * 1000
            X = der_obj.der_file.NP_REACTANCE * kV * kV / kVA * 1000
            self.dss.text(f'vsource.{name}_a.R0 = {R}')
            self.dss.text(f'vsource.{name}_a.R1 = {R}')
            self.dss.text(f'vsource.{name}_a.X0 = {X}')
            self.dss.text(f'vsource.{name}_a.X1 = {X}')
            self.dss.text(f'vsource.{name}_b.R0 = {R}')
            self.dss.text(f'vsource.{name}_b.R1 = {R}')
            self.dss.text(f'vsource.{name}_b.X0 = {X}')
            self.dss.text(f'vsource.{name}_b.X1 = {X}')
            self.dss.text(f'vsource.{name}_c.R0 = {R}')
            self.dss.text(f'vsource.{name}_c.R1 = {R}')
            self.dss.text(f'vsource.{name}_c.X0 = {X}')
            self.dss.text(f'vsource.{name}_c.X1 = {X}')
            self.dss.text(f'vsource.{name}_c.baseMVA = {kVA / 1000}')

        if self.DER_sim_type == 'generator':
            self.dss.text(f'generator.{name}.kVA = {der_obj.der_file.NP_VA_MAX / 1000}')
            self.dss.text(f'generator.{name}.kW = {der_obj.der_file.NP_P_MAX / 1000}')
            self.dss.text(f'generator.{name}.maxkvar = {der_obj.der_file.NP_Q_MAX_ABS / 1000}')
            self.dss.text(f'generator.{name}.minkvar = {-der_obj.der_file.NP_Q_MAX_INJ / 1000}')

    def load_scaling(self, mult=1.0):
        """
        Scaling all loads in the circuit simulation tool

        :param mult: Multiplication factor
        """
        # scale load
        for name in self.loads.index:
            if self.loads.loc[name, 'type'] == 'load':
                new_kw = self.loads.loc[name, 'kw'] * mult
                self.dss.loads.name = name
                self.dss.loads.kw = float(new_kw)

    def update_der_output_powers(self, der_list=None, p_list=None, q_list=None):
        """
        Update DER output information in terms of active and reactive power into the circuit simulation solver.
        p_list and q_list are used to specify P and Q values other than what are calculated in the OpenDER objects.
        Currently, this does not support DER as current source or voltage source behind impedance.

        :param der_list: Default is to update all DERs. If specified, only update part of the OpenDER objects.
        :param p_list: List of DER active power output in kW
        :param q_list: List of DER active power output in kvar
        """
        if p_list is not None and (self.DER_sim_type == 'isource' or self.DER_sim_type == 'vsource'):
            for der_obj, p, q in zip(der_list, p_list, q_list):
                p_pu = p * 1000 / der_obj.der_file.NP_VA_MAX
                q_pu = q * 1000 / der_obj.der_file.NP_VA_MAX
                der_obj.i_pos_pu, der_obj.i_neg_pu = der_obj.ridethroughperf.calculate_i_output(p_pu, q_pu)

        if p_list is None:
            p_list = [der_obj.p_out_kw for der_obj in der_list]

        if q_list is None:
            q_list = [der_obj.q_out_kvar for der_obj in der_list]

        for der_obj, P_gen, Q_gen in zip(der_list, p_list, q_list):

            name = der_obj.name
            if self.DER_sim_type == 'PVSystem':
                self.cmd(f'{self.DER_sim_type}.{name}.Pmpp={P_gen}')
                self.cmd(f'{self.DER_sim_type}.{name}.kvar={Q_gen}')

            if self.DER_sim_type == 'generator':
                self.cmd(f'{self.DER_sim_type}.{name}.kW={P_gen}')
                self.cmd(f'{self.DER_sim_type}.{name}.kvar={Q_gen}')

            if self.DER_sim_type == 'isource':
                (ia, ib, ic), (theta_a, theta_b, theta_c) = der_obj.get_der_output(output='I_A')

                self.cmd(f'{self.DER_sim_type}.{name}_a.amps={ia}')
                self.cmd(f'{self.DER_sim_type}.{name}_b.amps={ib}')
                self.cmd(f'{self.DER_sim_type}.{name}_c.amps={ic}')
                self.cmd(f'{self.DER_sim_type}.{name}_a.angle={theta_a * 57.29577951308232}')
                self.cmd(f'{self.DER_sim_type}.{name}_b.angle={theta_b * 57.29577951308232}')
                self.cmd(f'{self.DER_sim_type}.{name}_c.angle={theta_c * 57.29577951308232}')

            if self.DER_sim_type == 'vsource':
                (va, vb, vc), (theta_a, theta_b, theta_c) = der_obj.get_der_output(output='V_pu')

                self.cmd(f'{self.DER_sim_type}.{name}_a.pu={va * 0.577350}')
                self.cmd(f'{self.DER_sim_type}.{name}_b.pu={vb * 0.577350}')
                self.cmd(f'{self.DER_sim_type}.{name}_c.pu={vc * 0.577350}')
                self.cmd(f'{self.DER_sim_type}.{name}_a.angle={theta_a * 57.29577951308232}')
                self.cmd(f'{self.DER_sim_type}.{name}_b.angle={theta_b * 57.29577951308232}')
                self.cmd(f'{self.DER_sim_type}.{name}_c.angle={theta_c * 57.29577951308232}')

    def solve_power_flow(self) -> None:
        """
        Solve circuit power flow using dss engine
        """
        self.dss.text("solve")

    def read_sys_voltage(self) -> pd.DataFrame:
        """
        Read and return bus voltages derived from circuit simulators

        :return: bus voltages in DataFrame, indexed by bus names. Also accessed by .buses
        """

        nodenames = self.dss.circuit.nodes_names
        temp = self.dss.circuit.buses_volts
        nodevolts = [temp[2 * ii] + 1j * temp[2 * ii + 1] for ii in range(len(nodenames))]
        self.nodevolts = pd.DataFrame(nodevolts, index=nodenames, columns=['volts'])

        nodeangles = [cmath.phase(temp[2 * ii] + 1j * temp[2 * ii + 1]) for ii in range(len((nodenames)))]
        busnames = self.buses.index
        for phase in ['A', 'B', 'C']:
            self.buses['Vpu_{}'.format(phase)] = np.array(self.dss.circuit.buses_vmag_pu)[
                self.buses['nodeIndex_{}'.format(phase)][busnames]]
            self.buses['Theta_{}'.format(phase)] = np.array(nodeangles)[
                self.buses['nodeIndex_{}'.format(phase)][busnames]]

        for phase in ['A', 'B', 'C']:
            self.buses.loc[self.buses[f'nodeIndex_{phase}'] == -1, 'Vpu_{}'.format(phase)] = float('nan')

        return self.buses

    def read_der_voltage(self, der_bus_list=None) -> list:
        """
        Return bus voltages for DERs, from circuit simulators

        :param der_bus_list: Default is all DER. If specified, only selected DERs
        :return: bus voltage magnitude information for a DER, in pu
        """
        if der_bus_list is None:
            der_bus_list = self.der_bus_list
        return [self.buses.loc[der_bus, ['Vpu_A', 'Vpu_B', 'Vpu_C']] for der_bus in der_bus_list]

    def read_der_voltage_angle(self, der_bus_list=None) -> list:
        """
        Return bus voltage angles for DERs, from circuit simulators

        :param der_bus_list: Default is all DER. If specified, only selected DERs
        :return: bus voltage angle information for a DER, in radian
        """
        if der_bus_list is None:
            der_bus_list = self.der_bus_list
        return [self.buses.loc[der_bus, ['Theta_A', 'Theta_B', 'Theta_C']] for der_bus in der_bus_list]

    def read_line_flow(self) -> pd.DataFrame:
        """
        Read and return power flow on all lines, obtained from circuit simulators
        :return: power flow information in DataFrame, indexed by line names. Also accessed by .lines
        """

        linenames = self.lines.index
        for linename in linenames:
            self.dss.circuit.set_active_element('line.{}'.format(linename))
            ii = 0
            phases_num = self.dss.cktelement.bus_names[0].split('.')[1:]
            phases = [chr(int(i) + 64) for i in phases_num]
            if phases == []:
                phases = ['A', 'B', 'C']

            for phase in phases:
                if ('_' + phase.lower() in linename) or ('_' + phase in linename) or (
                        not (('_a' in linename) or ('_b' in linename) or ('_c' in linename))):
                    v = self.dss.cktelement.voltages[2 * ii] + 1j * self.dss.cktelement.voltages[2 * ii + 1]
                    s = self.dss.cktelement.powers[2 * ii] + 1j * self.dss.cktelement.powers[2 * ii + 1]

                    # complex current in amps (bus1 --> bus2)
                    if abs(v) < 0.00001:
                        v = 0.00001
                    self.lines.loc[linename, 'flowI_{}'.format(phase)] = np.conjugate(s / v) * 1.e3
                    # complex power in kVA (bus1 --> bus2)
                    self.lines.loc[linename, 'flowS_{}'.format(phase)] = s
                    ii = ii + 1
        return self.lines

    def set_source_voltage(self, v_pu: float) -> None:
        """
        Set dss circuit substation bus voltage
        """
        self.dss.vsources.pu = v_pu

    '''
    Initialize "vrStates" based on dss file
    '''

    def __init_vr(self):
        # self.vrStates = []
        VR_names = list(self.dss.regcontrols.names)
        if VR_names[0] == 'NONE':
            VR_names = []
        # RegulatorByPhase type
        for vr_name in VR_names:
            vr = dict()
            vr['Ts'] = 100000
            # retrieve vr information from DSS circuit
            vr['Xfmr'] = self.cmd('? regcontrol.{}.transformer'.format(vr_name))
            vr['winding'] = int(self.cmd('? regcontrol.{}.winding'.format(vr_name)))
            vr['Vref'] = float(self.cmd('? regcontrol.{}.vreg'.format(vr_name)))
            vr['db'] = float(self.cmd('? regcontrol.{}.band'.format(vr_name)))
            vr['PT_Ratio'] = float(self.cmd('? regcontrol.{}.ptratio'.format(vr_name)))
            vr['CT_Primary'] = float(self.cmd('? regcontrol.{}.ctprim'.format(vr_name)))
            vr['LDC_R'] = float(self.cmd('? regcontrol.{}.R'.format(vr_name)))
            vr['LDC_X'] = float(self.cmd('? regcontrol.{}.X'.format(vr_name)))
            vr['delay'] = float(self.cmd('? regcontrol.{}.delay'.format(vr_name)))
            vr['tapdelay'] = float(self.cmd('? regcontrol.{}.tapdelay'.format(vr_name)))
            # get transformer information
            vr['phases'] = int(self.cmd('? transformer.{}.phases'.format(vr['Xfmr'])))
            buses = self.cmd('? transformer.{}.buses'.format(vr['Xfmr']))
            bus = buses.replace('[', '').replace(']', '').split(',')[:-1][vr['winding'] - 1]
            bus = bus.replace(' ', '')
            vr['regBus'] = []
            if vr['phases'] == 1:
                vr['regBus'].append(bus)
            else:
                for ph in [1, 2, 3]:
                    bus = bus.split('.')[0]
                    vr['regBus'].append('{}.{}'.format(bus, ph))

            self._VRs[vr_name] = vr

    def enable_control(self):
        """
        Enable voltage regulator controls in OpenDSS. This is usually for steady-state analysis
        or establish the initial condition for a dynamic analysis.
        """
        self.cmd('set controlmode=STATIC')

    def disable_control(self):
        """
        Disable voltage regulator controls in circuit simulation tool solver. This is usually for dynamic simulation
        """
        self.cmd('set controlmode=OFF')

    def read_vr(self):
        """
        Read voltage regulator tap information from OpenDSS circuit into "vtStates"
        """
        for vrname in self._VRs.keys():
            self._VRs[vrname]['tapPos'] = int(self.cmd('? regcontrol.{}.tapNum'.format(vrname)))
            print(self._VRs[vrname]['tapPos'])

    def write_vr(self):
        """
        Write voltage regulator tap information from "vtStates" into OpenDSS circuit simulation.
        """
        for vrname in self._VRs.keys():
            self.cmd('edit regcontrol.{} tapNum={}'.format(vrname, self._VRs[vrname]['UpdatedTap']))

    def read_vr_v_i(self, vrname):
        """
        Return VR voltage and current information from OpenDSS circuit

        :param vrname: name of voltage regulator
        :return: Voltage and current
        """
        # voltage
        Vpri = [self.nodevolts.loc[node, 'volts'] for node in self._VRs[vrname]['regBus']]
        # current
        iwdg = self.cmd('? transformer.{}.wdgcurrents'.format(self._VRs[vrname]['Xfmr'])).split(',')[:-1]
        imag = [float(iwdg[2 * ii]) for ii in range(int(len(iwdg) / 2))]
        iang = [float(iwdg[2 * ii + 1].replace('(', '').replace(')', '')) for ii in range(int(len(iwdg) / 2))]
        icplx = [imag[ii] * np.exp(1j * np.pi * iang[ii] / 180) for ii in range(len(imag))]
        if self._VRs[vrname]['winding'] == 1:
            Ipri = [icplx[2 * ii] for ii in range(int(len(icplx) / 2))]
        else:
            Ipri = [-icplx[2 * ii + 1] for ii in range(int(len(icplx) / 2))]
        return Vpri, Ipri
