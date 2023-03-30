import numpy as np
import os
import pathlib
import matplotlib.pyplot as plt
from opender_interface.opendss_interface import OpenDSSInterface
from opender_interface.opender_interface import DERModelInterface
from opender import DER
from opender_interface.time_plots import TimePlots
from opender_interface.xy_plot import XYPlots

# %%
# parameter calculation
vbase = 12
sbase = 5
xor = 5
zpu = 0.1


# line impedance
zbase = vbase ** 2 / sbase
rpu = zpu / np.sqrt(1 + xor ** 2)
xpu = rpu * xor
#
rohms = rpu * zbase
xohms = xpu * zbase

# substation initial voltage
vsub0 = 1.03

script_path = pathlib.Path(os.path.dirname(__file__))
circuit_folder = script_path.joinpath("circuit")
dss_file = circuit_folder.joinpath("single_vsource_gfov.dss")

# configure the dynamic simulation
delt = 0.0001  # sampling time step (s)


# %%
# run dss simulation
dss = OpenDSSInterface(dss_file, tstep=delt)
dss.initialize()

der_list = dss.create_opender_objs(p_dc_pu=1,
                                   DER_sim_type='vsource',
                                   CONST_Q_MODE_ENABLE = True,
                                   CONST_Q = 0,
                                   NP_Q_CAPABILITY_LOW_P = 'SAME',
                                   NP_ABNORMAL_OP_CAT = 'CAT_III'
                                   )


der_interface = DERModelInterface()

DER.t_s=delt


der_interface.der_convergence_process(dss)
dss.solve_power_flow()

# run time series simulation
tsim = 0
tevt1 = 0.2
tevt2 = 0.4
tend = 0.6  # total simulation time (s)

vsub = vsub0
plot_obj = TimePlots(3,1)
v_plt_load = XYPlots(der_list[0])
v_plt_derh = XYPlots(der_list[0])
v_plt_derl = XYPlots(der_list[0])

while tsim < tend:
    # step reference / perturbation

    if tsim >= tevt1:
        dss.cmd('fault.fault1.enabled=yes')
    if tsim >= tevt2:
        dss.cmd('open line.line1')

    dss.set_source_voltage(vsub)

    der_interface.run()

    dss.update_der_output_powers(der_list)

    dss.solve_power_flow()
    dss.read_line_flow()

    print(tsim, dss.dss.bus_pu_voltages(), (dss.lines[['flowS_A', 'flowS_B', 'flowS_C']])) #,'flowS_A', 'flowS_B', 'flowS_C'
    # log result
    plot_obj.add_to_traces(
        {
            # 'v': sum(list(dss.buses.loc['load', ['Vpu_A', 'Vpu_B', 'Vpu_C']]))/3
            'v_a': dss.buses.loc['der_h', ['Vpu_A']],
            'v_b': dss.buses.loc['der_h', ['Vpu_B']],
            'v_c': dss.buses.loc['der_h', ['Vpu_C']],
        },
        {
            # 'v': sum(list(dss.buses.loc['load', ['Vpu_A', 'Vpu_B', 'Vpu_C']]))/3
            'v_a': dss.buses.loc['der_l', ['Vpu_A']],
            'v_b': dss.buses.loc['der_l', ['Vpu_B']],
            'v_c': dss.buses.loc['der_l', ['Vpu_C']],
        },

        {
            'p_pu (DER)': der_list[0].p_out_pu,
            # 'p_kw_grid': -sum(dss.dss.cktelement_powers()[0:5:2])
            'p_pu (Grid)': sum(list(dss.lines.iloc[0][['flowS_A', 'flowS_B', 'flowS_C']])).real / 100
        },
    )
    # step tsim
    dss.read_sys_voltage()
    tsim = tsim + delt

plot_obj.prepare()
plot_obj.show()

v_plt_derh.prepare_v3_plot(xy=dss.buses.loc['der_h', ['Vpu_A','Vpu_B','Vpu_C','Theta_A','Theta_B','Theta_C']])
v_plt_derh.save_fig('derh1')
v_plt_derh.show()
v_plt_derl.prepare_v3_plot(xy=dss.buses.loc['der_l', ['Vpu_A','Vpu_B','Vpu_C','Theta_A','Theta_B','Theta_C']], l2l=True)
print(der_list[0].der_input)
v_plt_derl.save_fig('derl1')
v_plt_derl.show()