import numpy as np
import pandas as pd
import matplotlib.pyplot as plt    
import pathlib
import os
from opender_interface.opender_interface import OpenDERInterface
from opender_interface.opendss_interface import OpenDSSInterface
from opender_interface.time_plots import TimePlots

#%%

script_path = pathlib.Path(os.path.dirname(__file__))
circuit_folder = script_path.parents[0].joinpath("IEEE_34Bus")
dss_file = circuit_folder.joinpath("ieee34Mod2_der.dss")
load_file = script_path.joinpath("load_profile.xlsx")

# folder and files
home_folder = script_path.parents[0]
save_folder = home_folder.joinpath("sim_data")



#%%
# import load profile
load_profile = pd.read_excel(load_file, index_col=0)

tstep = 1

#%%

ckt_int = OpenDERInterface(str(dss_file), t_s=tstep)
ckt_int.initialize()

#%%
# set up simulation

#%%
# create voltage regulator controls to replace the ones in the circuit
vr_list = [
    {'name': 'creg1a', 'Td_ctrl': 30, 'Td_tap': 2},
    {'name': 'creg1b', 'Td_ctrl': 30, 'Td_tap': 2},
    {'name': 'creg1c', 'Td_ctrl': 30, 'Td_tap': 2},
    {'name': 'creg2a', 'Td_ctrl': 45, 'Td_tap': 2},
    {'name': 'creg2b', 'Td_ctrl': 45, 'Td_tap': 2},
    {'name': 'creg2c', 'Td_ctrl': 45, 'Td_tap': 2},
    ]

ckt_int.create_vr_objs(vr_list)
#
    
#%%
# connect a DER to each bus and create DER model interface
der_list = ckt_int.create_opender_objs(p_dc_pu=0.8, ES_RAMP_RATE=00, ES_RANDOMIZED_DELAY=300)


#%%
# add a fault branch to the circuit, disable the fault by setting very high impedance
ckt_int.ckt.cmd('New Fault.F1 Phases=3 Bus1={}'.format('808'))
ckt_int.ckt.cmd('Edit Fault.F1 R=1000000')


# run a load flow and check the feeder total power
sim_data = []
t = 0
plot_obj = TimePlots(3,1)

# Initialize
ckt_int.ckt.enable_control()
mult = np.interp(0, load_profile.index, load_profile['mult'])
ckt_int.ckt.load_scaling(mult)
ckt_int.der_convergence_process()
ckt_int.ckt.read_vr()
ckt_int.ckt.update_vr_tap()
ckt_int.ckt.disable_control()


while t < 1200:
    # event simulation
    if t > 45 and t < 50:
        ckt_int.ckt.cmd('Edit Fault.F1 R=0.01')
    else:
        ckt_int.ckt.cmd('Edit Fault.F1 R=1000000')

    ckt_int.read_sys_voltage()

    # simulate der dynamics
    ckt_int.run()


    # get der injection
    total_gen_kw = 0

    ckt_int.update_der_output_powers()
    kw = sum([der.p_out_kw for der in ckt_int.der_objs])

    # # change load level
    mult = np.interp(t, load_profile.index, load_profile['mult'])
    ckt_int.ckt.load_scaling(mult)
    
    # solve load flow
    ckt_int.ckt.cmd('solve')

    # simulate vr control
    for vr in ckt_int.ckt.vrStates:
        Vpri, Ipri = ckt_int.ckt.read_vr_v_i(vr)
        # run the vr control logic
        vr['model'].run(Vpri = Vpri, Ipri = Ipri)

    # set the new tap position into opendss
    ckt_int.ckt.write_vr()
    
    # save result
    result1 = {}
    result2 = {}
    result3 = {}
    result4 = {}

    for der in ckt_int.der_objs:
        result1['q_out_pu({})'.format(der.name)] = der.q_out_kvar / der.der_file.NP_VA_MAX
        # result['qout({})'.format(der.name)] = der.q_out_kvar
        result3['v({})'.format(der.name)] = der.der_input.v_meas_pu
        # result3[f'debug({der.name})'] = der.enterservice.vft_delay.con_del_enable_out
        # result4[f'{der.name}'] = der.enterservice.vft_delay.con_del_enable_int

    for vr in ckt_int.ckt.vrStates:
        a = vr['name']
        # phase = vr['phase']
        result4[f'Tap ({a})'] = vr['model'].tap
        result2[f'V ({a})'] = vr['model'].V

    plot_obj.add_to_traces(
        {
            'total_load_kw': mult * 1749,
            'total_gen_kw': sum([der.p_out_kw for der in ckt_int.der_objs])
        },
        result2, result4
    )
    t = t + tstep


a = [vr['model'].total_sw for vr in ckt_int.ckt.vrStates]
print(a, sum(a))

plot_obj.prepare()
for ax in plot_obj.axes:
    # ax.get_legend().remove()
    ax.grid(visible=True)
    ax.legend(loc=1)  # ,fontsize='x-small')
    ax.set_title(' ')

plot_obj.fig.set_size_inches(6, 6)
plot_obj.axes[1].set_ylim(115, 132)
plot_obj.axes[0].set_xlim(0, 1500)

plt.tight_layout()

# plot_obj.save(save_folder.joinpath('simplot2.svg'), save_folder.joinpath('simplot2.pkl'))
plot_obj.show()

