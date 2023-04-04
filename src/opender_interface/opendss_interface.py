import py_dss_interface
import numpy as np
import pandas as pd
import cmath
from opender_interface.simulation_interface import SimulationInterfacesABC
from opender.der import DER
from .voltage_regulator import VR_Model

class OpenDSSInterface(SimulationInterfacesABC):

    def __init__(self, dss_file: str, tstep=100000) -> None:

        self.dss_file = dss_file
        self.dss = py_dss_interface.DSSDLL()
        self.der_bus_list = []

        self.dss.text(f"Compile [{self.dss_file}]")

        self.tstep = tstep


    def cmd(self,cmd_line):
        if type(cmd_line) is list:
            return [self.dss.text(cmd) for cmd in cmd_line]
        elif type(cmd_line) is str:
            return self.dss.text(cmd_line)
        else:
            raise ValueError("OpenDSS Initializing cmd_list is not valid")


    def initialize(self, DER_sim_type = 'PVSystem'):
        self.init_buses()
        self.init_lines()
        self.init_loads()
        self.init_generators()
        self.init_PVSystems()
        self.init_vr()
        self.DER_sim_type = DER_sim_type

        if DER_sim_type == 'PVSystem':
            self.init_PVSystems()
            self.DER_sim_type = 'PVSystem'
        if DER_sim_type == 'isource':
            self.init_isources()
            self.DER_sim_type = 'isource'
        if DER_sim_type == 'vsource':
            self.init_vsources()
            self.DER_sim_type = 'vsource'

    def init_buses(self):
        nodenames = list(self.dss.circuit_all_node_names())
        buses = []
        for busname in self.dss.circuit_all_bus_names():
            self.dss.circuit_set_active_bus(busname)
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
                'kVBaseLL': self.dss.bus_kv_base() * np.sqrt(3),
                'nPhases': self.dss.bus_num_nodes(),
                'distance': self.dss.bus_distance() * 0.621371, #km to miles
                'x': self.dss.bus_read_x(),
                'y': self.dss.bus_read_y(),
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

    def init_lines(self):
        linenames = list(self.dss.lines_all_names())
        lines = []
        for linename in linenames:
            self.dss.lines_write_name(linename)
            bus1 = self.dss.lines_read_bus1().split('.')[0]
            bus2 = self.dss.lines_read_bus2().split('.')[0]
            self.dss.circuit_set_active_bus(bus1)
            lines.append({
                'name': linename,
                'bus1': bus1,
                'bus2': bus2,
                'kVBaseLN': self.dss.bus_kv_base(),
                'nPhases': self.dss.lines_read_phases(),
                'length': self.dss.lines_read_length(),
                'normamps': self.dss.lines_read_norm_amps(),
                'emergamps': self.dss.lines_read_emerg_amps(),
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

    def init_loads(self):
        loadnames = self.dss.loads_all_names()
        loads = []
        for loadname in loadnames:
            self.dss.loads_write_name(loadname)
            kw = self.dss.loads_read_kw()
            bus = self.dss.text(f'? load.{loadname}.bus1')
            phases = int(self.dss.text(f'? load.{loadname}.phases'))
            # if loadname[0].lower() == 'l':
            #     this_type = 'load'
            # else:
            #     this_type = 'gen'
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

    def init_generators(self):
        gennames = list(self.dss.generators_all_names())
        gens = []
        for genname in gennames:
            self.dss.generators_write_name(genname)
            kw = self.dss.generators_read_kw()
            kvar = self.dss.generators_read_kvar()
            kVA = self.dss.generators_read_kva_rated()
            self.dss.pvsystems_kw()
            bus = self.dss.text(f'? generator.{genname}.bus1')
            this_type = 'generator'
            gens.append({
                'name':genname,
                'type': this_type,
                'bus': bus.split('.')[0].replace(' ', ''),
                'kw': kw,
                'kvar': kvar,
                'kVA': kVA,
            })

        self.generators = pd.DataFrame(gens)
        # self.generators.set_index('name', inplace=True)

    def init_PVSystems(self):
        PVnames = list(self.dss.pvsystems_all_names())
        PVs = []
        for PVname in PVnames:
            self.dss.pvsystems_write_name(PVname)
            kw = self.dss.pvsystems_read_pmpp()
            # kvar = self.ckt_int.pvsystems_read_kvar() #TODO check with Paulo, seems that it always get 0
            kVA = self.dss.pvsystems_read_kva_rated()
            bus = self.dss.text(f'? PVSystem.{PVname}.bus1')
            kvar = float(self.dss.text(f'? PVSystem.{PVname}.kvarmax'))
            kvarabs = float(self.dss.text(f'? PVSystem.{PVname}.kvarmaxabs'))
            kV = float(self.dss.text(f'? PVSystem.{PVname}.kv'))
            this_type = 'PVSystem'
            PVs.append({ #TODO make consistent with CYMEInterface
                'name':PVname,
                'type': this_type,
                'bus': bus.split('.')[0].replace(' ', ''),
                'kw': kw,
                'kvar': kvar,
                'kvarabs': kvarabs,
                'kVA': kVA,
                'kV':kV
            })
            self.der_bus_list.append(bus.split('.')[0].replace(' ', ''))

        self.DERs = pd.DataFrame(PVs)
        # self.DERs.set_index('name', inplace=True)

    def init_isources(self):
        PVnames = list(self.dss.isources_all_names())
        PVs = []
        PVnames = [PVname.split('_')[0].replace(' ', '') for PVname in PVnames]
        PVnames = [*set(PVnames)]
        for PVname in PVnames:
            self.dss.isources_write_name(f'{PVname}_a')
            # kw = self.ckt_int.pvsystems_read_pmpp()
            # kVA = self.ckt_int.pvsystems_read_kva_rated()
            bus = self.dss.text(f'? isource.{PVname}_a.bus1')
            # kvar = float(self.ckt_int.text(f'? PVSystem.{PVname}.kvarmax'))
            # kvarabs = float(self.ckt_int.text(f'? PVSystem.{PVname}.kvarmaxabs'))
            self.dss.circuit_set_active_bus(bus)
            kV = self.dss.bus_kv_base() * 1.7320508075688 #TODO make sure this is correct

            this_type = 'isource'
            PVs.append({  # TODO make consistent with CYMEInterface
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

        self.DERs = pd.DataFrame(PVs)
        # self.DERs.set_index('name', inplace=True)

    def init_vsources(self):
        PVnames = list(self.dss.vsources_all_names())[1:]
        PVs = []
        PVnames = [PVname.split('_')[0].replace(' ', '') for PVname in PVnames]
        PVnames = [*set(PVnames)]
        for PVname in PVnames:
            self.dss.vsources_write_name(f'{PVname}_a')
            kw = float(self.dss.text(f'? vsource.{PVname}_a.baseMVA')) * 1000
            kVA = float(self.dss.text(f'? vsource.{PVname}_a.baseMVA')) * 1000
            bus = self.dss.text(f'? vsource.{PVname}_a.bus1')
            # kvar = float(self.ckt_int.text(f'? PVSystem.{PVname}.kvarmax'))
            # kvarabs = float(self.ckt_int.text(f'? PVSystem.{PVname}.kvarmaxabs'))
            self.dss.circuit_set_active_bus(bus)
            kV = self.dss.bus_kv_base() * 1.7320508075688 #TODO make sure this is correct
            R = 0.001 * kV * kV / kw * 1000
            X = 0.2 * kV * kV / kw * 1000
            self.dss.text(f'vsource.{PVname}_a.R0 = {R}')
            self.dss.text(f'vsource.{PVname}_a.R1 = {R}')
            self.dss.text(f'vsource.{PVname}_a.X0 = {X}')
            self.dss.text(f'vsource.{PVname}_a.X1 = {X}')
            self.dss.text(f'vsource.{PVname}_b.R0 = {R}')
            self.dss.text(f'vsource.{PVname}_b.R1 = {R}')
            self.dss.text(f'vsource.{PVname}_b.X0 = {X}')
            self.dss.text(f'vsource.{PVname}_b.X1 = {X}')
            self.dss.text(f'vsource.{PVname}_c.R0 = {R}')
            self.dss.text(f'vsource.{PVname}_c.R1 = {R}')
            self.dss.text(f'vsource.{PVname}_c.X0 = {X}')
            self.dss.text(f'vsource.{PVname}_c.X1 = {X}')
            this_type = 'vsource'
            PVs.append({  # TODO make consistent with CYMEInterface
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

        self.DERs = pd.DataFrame(PVs)


    def load_scaling(self, mult=1.0):
        # scale load
        for name in self.loads.index:
            if self.loads.loc[name, 'type'] == 'load':
                new_kw = self.loads.loc[name, 'kw'] * mult
                self.dss.loads_write_name(name)
                self.dss.loads_write_kw(float(new_kw))


    # update DER output P/Q to circuit simulation
    def update_der_output_powers(self, der_list=None, p_list=None, q_list=None):

        if p_list is not None and (self.DER_sim_type == 'isource' or self.DER_sim_type == 'vsource'):
            for der_obj, p, q in zip(der_list, p_list, q_list):
                p_pu = p *1000 / der_obj.der_file.NP_VA_MAX
                q_pu = q *1000 / der_obj.der_file.NP_VA_MAX
                der_obj.i_pos_pu, der_obj.i_neg_pu = der_obj.ridethroughperf.calculate_i_output(p_pu,q_pu)

        if p_list is None:
            p_list = [der_obj.p_out_kw for der_obj in der_list]

        if q_list is None:
            q_list = [der_obj.q_out_kvar for der_obj in der_list]

        for der_obj, P_gen, Q_gen in zip(der_list, p_list, q_list):
            # kw = der_obj.p_out_kw
            # kvar = der_obj.q_out_kvar
            name = der_obj.name
            if self.DER_sim_type == 'PVSystem':
                self.cmd(f'{self.DER_sim_type}.{name}.Pmpp={P_gen}')
                self.cmd(f'{self.DER_sim_type}.{name}.kvar={Q_gen}')
            if self.DER_sim_type == 'isource':
                (ia, ib, ic), (theta_a, theta_b, theta_c) = der_obj.get_der_output(output='I_A')

                self.cmd(f'{self.DER_sim_type}.{name}_a.amps={ia}')
                self.cmd(f'{self.DER_sim_type}.{name}_b.amps={ib}')
                self.cmd(f'{self.DER_sim_type}.{name}_c.amps={ic}')
                self.cmd(f'{self.DER_sim_type}.{name}_a.angle={theta_a*57.29577951308232}')
                self.cmd(f'{self.DER_sim_type}.{name}_b.angle={theta_b*57.29577951308232}')
                self.cmd(f'{self.DER_sim_type}.{name}_c.angle={theta_c*57.29577951308232}')

            if self.DER_sim_type == 'vsource':
                (va, vb, vc), (theta_a, theta_b, theta_c) = der_obj.get_der_output(output='V_pu')

                self.cmd(f'{self.DER_sim_type}.{name}_a.pu={va* 0.577350}')
                self.cmd(f'{self.DER_sim_type}.{name}_b.pu={vb*0.577350}')
                self.cmd(f'{self.DER_sim_type}.{name}_c.pu={vc*0.577350}')
                self.cmd(f'{self.DER_sim_type}.{name}_a.angle={theta_a * 57.29577951308232}')
                self.cmd(f'{self.DER_sim_type}.{name}_b.angle={theta_b * 57.29577951308232}')
                self.cmd(f'{self.DER_sim_type}.{name}_c.angle={theta_c * 57.29577951308232}')

        # self.ckt_int.text(f"edit generator.{self.ckt_int.generators_read_name()} "
        #               f"kw={p_out_kw} "
        #               f"kvar={q_out_kvar}")


    def solve_power_flow(self) -> None:
        self.dss.text("solve")



    def read_sys_voltage(self):
        nodenames = self.dss.circuit_all_node_names()
        temp = self.dss.circuit_all_bus_volts()
        nodevolts = [temp[2 * ii] + 1j * temp[2 * ii + 1] for ii in range(len(nodenames))]
        self.nodevolts = pd.DataFrame(nodevolts, index=nodenames, columns=['volts'])

        nodeangles = [cmath.phase(temp[2 * ii] + 1j * temp[2 * ii + 1]) for ii in range(len((nodenames)))]
        busnames = self.buses.index
        for phase in ['A', 'B', 'C']:
            self.buses['Vpu_{}'.format(phase)] = np.array(self.dss.circuit_all_bus_vmag_pu())[self.buses['nodeIndex_{}'.format(phase)][busnames]]
            self.buses['Theta_{}'.format(phase)] = np.array(nodeangles)[self.buses['nodeIndex_{}'.format(phase)][busnames]]

                
        for phase in ['A', 'B', 'C']:
            self.buses.loc[ self.buses[f'nodeIndex_{phase}'] == -1,'Vpu_{}'.format(phase)] = float('nan')

        # busVmagPu = self.buses[['Vpu_A','Vpu_B','Vpu_C']].mean(axis=1)

    def read_der_voltage(self, der_bus_list=None):
        if der_bus_list==None:
            der_bus_list = self.der_bus_list
        return [self.buses.loc[der_bus, ['Vpu_A', 'Vpu_B', 'Vpu_C']] for der_bus in der_bus_list]

    def read_der_voltage_angle(self, der_bus_list=None):
        if der_bus_list==None:
            der_bus_list = self.der_bus_list
        return [self.buses.loc[der_bus, ['Theta_A', 'Theta_B', 'Theta_C']] for der_bus in der_bus_list]

    def read_line_flow(self):
        linenames = self.lines.index
        for linename in linenames:
            self.dss.circuit_set_active_element('line.{}'.format(linename))
            ii = 0
            phases_num = self.dss.cktelement_read_bus_names()[0].split('.')[1:]
            phases = [chr(int(i)+64) for i in phases_num]

            for phase in phases:
                if ('_'+phase.lower() in linename) or ('_'+phase in linename) or (not(('_a' in linename)or('_b' in linename)or('_c' in linename))):
                    v = self.dss.cktelement_voltages()[2 * ii] + 1j * self.dss.cktelement_voltages()[2 * ii + 1]
                    s = self.dss.cktelement_powers()[2 * ii] + 1j * self.dss.cktelement_powers()[2 * ii + 1]
                    # complex current in amps (bus1 --> bus2)
                    if abs(v)<0.00001:
                        v=0.00001
                    self.lines.loc[linename, 'flowI_{}'.format(phase)] = np.conjugate(s / v) * 1.e3
                    # complex power in kVA (bus1 --> bus2)
                    self.lines.loc[linename, 'flowS_{}'.format(phase)] = s
                    ii = ii + 1

    def set_source_voltage(self, v_pu: float) -> None:
        self.dss.vsources_write_pu(v_pu)


    def init_vr(self):
        self.vrStates = []
        VR_names = list(self.dss.regcontrols_all_names())
        # RegulatorByPhase type
        for vr_name in VR_names:
            vr=dict()
            vr['Ts'] = self.tstep
            # retrieve vr information from DSS circuit
            vr['Xfmr'] = self.cmd('? regcontrol.{}.transformer'.format(vr_name))
            vr['winding'] = int(self.cmd('? regcontrol.{}.winding'.format(vr_name)))
            vr['Vref'] = float(self.cmd('? regcontrol.{}.vreg'.format(vr_name)))
            vr['db'] = float(self.cmd('? regcontrol.{}.band'.format(vr_name)))
            vr['PT_Ratio'] = float(self.cmd('? regcontrol.{}.ptratio'.format(vr_name)))
            vr['CT_Primary'] = float(self.cmd('? regcontrol.{}.ctprim'.format(vr_name)))
            vr['LDC_R'] = float(self.cmd('? regcontrol.{}.R'.format(vr_name)))
            vr['LDC_X'] = float(self.cmd('? regcontrol.{}.X'.format(vr_name)))
            # get transformer information
            vr['phases'] = int(self.cmd('? transformer.{}.phases'.format(vr['Xfmr'])))
            buses = self.cmd('? transformer.{}.buses'.format(vr['Xfmr']))
            bus = buses.replace('[', '').replace(']', '').split(',')[:-1][vr['winding'] - 1]
            bus = bus.replace(' ', '')
            vr['regBus'] = []
            vr['name']=vr_name
            if vr['phases'] == 1:
                vr['regBus'].append(bus)
            else:
                for ph in [1, 2, 3]:
                    bus = bus.split('.')[0]
                    vr['regBus'].append('{}.{}'.format(bus, ph))

            self.vrStates.append(vr)

    def create_vr_objs(self,vr_list):
        for vr in vr_list:
            for fdr_vr in self.vrStates:
                if fdr_vr['name'] == vr['name']:
                    fdr_vr['model'] = VR_Model(
                        Ts=self.tstep,
                        Td_ctrl=vr['Td_ctrl'],
                        Td_tap=vr['Td_tap'],
                        Vref=fdr_vr['Vref'],
                        db=fdr_vr['db'],
                        LDC_R=fdr_vr['LDC_R'],
                        LDC_X=fdr_vr['LDC_X'],
                        PT_Ratio=fdr_vr['PT_Ratio'],
                        CT_Primary=fdr_vr['CT_Primary'],
                        tap_ini=0,
                    )

    # enable time dependent component action for snapshot analysis or initial power flow
    def enable_control(self):
        self.cmd('set controlmode=STATIC')

    # disable time dependent component action dynamic simulation
    def disable_control(self):
        self.cmd('set controlmode=OFF')

    def read_vr(self):
        for vr in self.vrStates:
            vr['tapPos'] = int(self.cmd('? regcontrol.{}.tapNum'.format(vr['name'])))
            print(vr['tapPos'])

    def update_vr_tap(self):
        for vr in self.vrStates:
            vr['model'].tap = float(vr['tapPos'])

    def write_vr(self):
        for vr in self.vrStates:
            self.cmd('edit regcontrol.{} tapNum={}'.format(vr['name'], vr['model'].tap))

    def read_vr_v_i(self, vr):
        # voltage
        Vpri = [self.nodevolts.loc[node, 'volts'] for node in vr['regBus']]
        # current
        iwdg = self.cmd('? transformer.{}.wdgcurrents'.format(vr['Xfmr'])).split(',')[:-1]
        imag = [float(iwdg[2 * ii]) for ii in range(int(len(iwdg) / 2))]
        iang = [float(iwdg[2 * ii + 1].replace('(', '').replace(')', '')) for ii in range(int(len(iwdg) / 2))]
        icplx = [imag[ii] * np.exp(1j * np.pi * iang[ii] / 180) for ii in range(len(imag))]
        if vr['winding'] == 1:
            Ipri = [icplx[2 * ii] for ii in range(int(len(icplx) / 2))]
        else:
            Ipri = [-icplx[2 * ii + 1] for ii in range(int(len(icplx) / 2))]
        return Vpri, Ipri
