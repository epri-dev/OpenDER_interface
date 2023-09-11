import numpy as np
import pandas as pd
import matplotlib.pyplot as plt    
import pathlib
import os
from opender_interface.der_interface import DERInterface
from opender_interface.opendss_interface import OpenDSSInterface
from opender_interface.time_plots import TimePlots
from opender import DERCommonFileFormat

#%%

"""
This example demonstrates the DER enter service performance and its interactions with voltage regulators.
"""

# circuit path
script_path = pathlib.Path(os.path.dirname(__file__))
circuit_folder = script_path.parents[0].joinpath("IEEE_34Bus")
dss_file = circuit_folder.joinpath("ieee34Mod2_der.dss")
load_file = script_path.joinpath("load_profile.xlsx")

# import load profile
load_profile = pd.read_excel(load_file, index_col=0)

# simulation time step
tstep = 1

# Create DERInterface
ckt = OpenDSSInterface(str(dss_file))
ckt_int = DERInterface(ckt, t_s=tstep)

# initialize circuit
ckt_int.initialize()

# create voltage regulator controls objects to replace the ones in the circuit
ckt_int.create_vr_objs()

# connect a DER to each bus and create DER model interface
der_file = DERCommonFileFormat(NP_VA_MAX=300000,
                               NP_P_MAX=300000,
                               NP_Q_MAX_INJ=132000,
                               NP_Q_MAX_ABS=132000,
                               QV_MODE_ENABLE=True,

                               ES_DELAY=300,
                               ES_RAMP_RATE=0,
                               ES_RANDOMIZED_DELAY=0,)

der_list = ckt_int.create_opender_objs(p_pu=1,der_files=der_file)


# add a fault branch to the circuit, disable the fault by setting very high impedance
ckt_int.cmd('New Fault.F1 Phases=3 Bus1={}'.format('808'))
ckt_int.cmd('Edit Fault.F1 R=1000000')

t = 0
plot_obj = TimePlots(3, 1, ['DER output Power (kW)', 'Voltage Regulator Voltages (120V)', 'Voltage Regulator Tap Position'])

# Initialize
ckt_int.enable_control()
# mult = np.interp(0, load_profile.index, load_profile['mult'])
# ckt_int.load_scaling(mult)
ckt_int.der_convergence_process()
ckt_int.read_vr()
ckt_int.update_vr_tap()
ckt_int.disable_control()

# dynamic simulation
while t < 1200:

    # event simulation
    if 45 < t < 50:
        ckt_int.cmd('Edit Fault.F1 R=0.01')
    else:
        ckt_int.cmd('Edit Fault.F1 R=1000000')

    ckt_int.read_sys_voltage()

    # simulate der dynamics
    ckt_int.run()

    # get der injection
    total_gen_kw = 0

    ckt_int.update_der_output_powers()
    kw = sum([der.p_out_kw for der in ckt_int.der_objs])

    # change load level
    mult = np.interp(t, load_profile.index, load_profile['mult'])
    # ckt_int.load_scaling(mult)
    
    # solve load flow
    ckt_int.solve_power_flow()

    # simulate vr control
    for vrname in ckt_int.ckt.VRs.keys():
        Vpri, Ipri = ckt_int.read_vr_v_i(vrname)
        # run the vr control logic
        ckt_int.vr_objs[vrname].run(Vpri = Vpri, Ipri = Ipri)

    # set the new tap position into opendss
    ckt_int.write_vr()
    
    # save result
    result1 = {}
    result2 = {}
    result3 = {}
    result4 = {}

    for der in ckt_int.der_objs:
        result1['q_out_pu({})'.format(der.name)] = der.p_out_pu
        # result['qout({})'.format(der.name)] = der.q_out_kvar
        result3['v({})'.format(der.name)] = der.der_input.v_meas_pu
        # result3[f'debug({der.name})'] = der.enterservice.vft_delay.con_del_enable_out
        # result4[f'{der.name}'] = der.enterservice.vft_delay.con_del_enable_int

    for vrname in ckt_int.ckt.VRs.keys():
        if vrname[-1]=='a':
            result4[f'Tap ({vrname})'] = ckt_int.vr_objs[vrname].tap
            result2[f'V ({vrname})'] = ckt_int.vr_objs[vrname].V

    plot_obj.add_to_traces(
        {
            # 'total_load_kw': mult * 1749,
            'Total DER Power (kw)': sum([der.p_out_kw for der in ckt_int.der_objs])
        },
        # result1,
        result2, result4
    )
    t = t + tstep
print('-------------------------------------------------------------')
print(f'Total number of tap operations is {sum([ckt_int.vr_objs[vrname].total_sw for vrname in ckt_int.ckt.VRs.keys()])}')
# plot figure
plot_obj.prepare()
for ax in plot_obj.axes:
    # ax.get_legend().remove()
    ax.grid(visible=True)
    ax.legend()  # ,fontsize='x-small')
    # ax.set_title(' ')

plot_obj.fig.set_size_inches(4, 6)
plot_obj.axes[1].set_ylim(115, 132)
plot_obj.axes[0].set_xlim(0, 1500)

plt.tight_layout()

# plot_obj.save('simplot2.svg')
plot_obj.show()

