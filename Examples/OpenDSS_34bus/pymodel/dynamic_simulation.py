import numpy as np
import pandas as pd
import matplotlib.pyplot as plt    
import pathlib
import os
from opender_interface.opender_interface import DERModelInterface
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

fdr = OpenDSSInterface(str(dss_file), tstep=tstep)
fdr.initialize()

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

fdr.create_vr_objs(vr_list)
#
    
#%%
# connect a DER to each bus and create DER model interface
der_interface = fdr.create_opender_objs(p_dc_pu=0.8, ES_RAMP_RATE=00, ES_RANDOMIZED_DELAY=300)


#%%
# add a fault branch to the circuit, disable the fault by setting very high impedance
fdr.cmd('New Fault.F1 Phases=3 Bus1={}'.format('808'))
fdr.cmd('Edit Fault.F1 R=1000000')


# run a load flow and check the feeder total power
sim_data = []
t = 0
plot_obj = TimePlots(3,1)

# Initialize
fdr.enable_control()
mult = np.interp(0, load_profile.index, load_profile['mult'])
fdr.load_scaling(mult)
der_interface.der_convergence_process()
fdr.read_vr()
fdr.update_vr_tap()
fdr.disable_control()


while t < 1200:
    # event simulation
    if t > 45 and t < 50:
        fdr.cmd('Edit Fault.F1 R=0.01')
    else:
        fdr.cmd('Edit Fault.F1 R=1000000')

    fdr.read_sys_voltage()

    # simulate der dynamics
    v_der_list = fdr.read_der_voltage()
    der_interface.run()


    # get der injection
    total_gen_kw = 0

    fdr.update_der_output_powers()
    kw = sum([der.p_out_kw for der in der_interface.der_objs])

    # # change load level
    mult = np.interp(t, load_profile.index, load_profile['mult'])
    fdr.load_scaling(mult)
    
    # solve load flow
    fdr.cmd('solve')

    # simulate vr control
    for vr in fdr.vrStates:
        Vpri, Ipri = fdr.read_vr_v_i(vr)
        # run the vr control logic
        vr['model'].run(Vpri = Vpri, Ipri = Ipri)

    # set the new tap position into opendss
    fdr.write_vr()
    
    # save result
    result1 = {}
    result2 = {}
    result3 = {}
    result4 = {}

    for der in der_interface.der_objs:
        result1['q_out_pu({})'.format(der.name)] = der.q_out_kvar / der.der_file.NP_VA_MAX
        # result['qout({})'.format(der.name)] = der.q_out_kvar
        result3['v({})'.format(der.name)] = der.der_input.v_meas_pu
        # result3[f'debug({der.name})'] = der.enterservice.vft_delay.con_del_enable_out
        # result4[f'{der.name}'] = der.enterservice.vft_delay.con_del_enable_int

    for vr in fdr.vrStates:
        a = vr['name']
        # phase = vr['phase']
        result4[f'Tap ({a})'] = vr['model'].tap
        result2[f'V ({a})'] = vr['model'].V

    plot_obj.add_to_traces(
        {
            'total_load_kw': mult * 1749,
            'total_gen_kw': sum([der.p_out_kw for der in der_interface.der_objs])
        },
        result2, result4
    )
    t = t + tstep


a = [vr['model'].total_sw for vr in fdr.vrStates]
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

