import numpy as np
import os
import pathlib
from opender_interface.der_interface import DERInterface
from opender import DER, DERCommonFileFormat, DERCommonFileFormatBESS
from opender_interface.time_plots import TimePlots
from opender_interface.opendss_interface import OpenDSSInterface

'''
This is an example illustrating the utilization of BESS for peak shaving of PV power in a 15-minute time series.
'''

# %%
# circuit configuration path
script_path = pathlib.Path(os.path.dirname(__file__))
circuit_folder = script_path
dss_file = circuit_folder.joinpath("dss_BESS_PV.dss")

# configure the dynamic simulation
delt = 60 * 15  # sampling time step (s)


# %%
# create DERInterface
ckt_int = DERInterface(dss_file, t_s=delt)

# create DER object PV and BESS
derfiles = {
    'PV1': DERCommonFileFormat(NP_P_MAX=1000000, NP_VA_MAX=1000000, NP_Q_MAX_INJ=440000, NP_Q_MAX_ABS=440000),

    'BESS1': DERCommonFileFormatBESS(NP_P_MAX=1000000, NP_VA_MAX=1000000, NP_Q_MAX_INJ=440000, NP_Q_MAX_ABS=440000,
                                     NP_P_MAX_CHARGE=1000000, NP_APPARENT_POWER_CHARGE_MAX=1000000,
                                     QV_MODE_ENABLE=True, NP_BESS_CAPACITY=2000000)
}
ckt_int.initialize(DER_sim_type='generator')

der_list = ckt_int.create_opender_objs(derfiles,p_pu=0)

DER.t_s=delt

ckt_int.der_convergence_process()
# ckt_int.solve_power_flow()


tsim = 0

plot_obj = TimePlots(4,1, ['Voltage [pu]', 'Power [pu]', 'Reactive Power [pu]', 'BESS State of Charge [pu]'])

PV_profile = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.000515464, 0.003608247, 0.009278351, 0.018041237,
              0.034536082, 0.027319588, 0.032474227, 0.086597938, 0.099484536, 0.128865979, 0.024226804, 0.02628866, 0.060309278,
              0.484536082, 0.752061856, 0.782474227, 0.527835052, 0.853092784, 0.857216495, 0.853608247, 0.843814433, 0.834536082,
              0.819587629, 0.807731959, 0.791237113, 0.765463918, 0.731958763, 0.70257732, 0.667010309, 0.631958763, 0.586082474,
              0.539175258, 0.486597938, 0.424226804, 0.351546392, 0.263917526, 0.153608247, 0.12628866, 0.05257732, 0.004639175,
              0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
              0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
              0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.002061856, 0.009278351, 0.063402062, 0.146907216, 0.347938144,
              0.42628866, 0.494845361, 0.559793814, 0.616494845, 0.669587629, 0.721649485, 0.76443299, 0.798969072, 0.833505155,
              0.857216495, 0.874226804, 0.88556701, 0.906185567, 0.913402062, 0.920618557, 0.919587629, 0.91443299, 0.906701031,
              0.896907216, 0.879896907, 0.851546392, 0.834020619, 0.801030928, 0.767525773, 0.727835052, 0.682474227, 0.631958763,
              0.580927835, 0.52371134, 0.460824742, 0.380927835, 0.286597938, 0.171649485, 0.13814433, 0.060824742, 0.007216495,
              0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
              0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
              0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.001546392, 0.009278351, 0.071134021, 0.143298969, 0.33556701,
              0.422164948, 0.495360825, 0.561340206, 0.619587629, 0.672164948, 0.718556701, 0.758247423, 0.795876289, 0.828350515,
              0.848969072, 0.871649485, 0.896391753, 0.909278351, 0.902061856, 0.908247423, 0.912371134, 0.912886598, 0.908762887,
              0.892783505, 0.874742268, 0.85, 0.831958763, 0.79742268, 0.76443299, 0.725773196, 0.684020619, 0.63556701, 0.584536082,
              0.528865979, 0.464948454, 0.382474227, 0.293814433, 0.179896907, 0.140721649, 0.066494845, 0.008762887, 0.0,
              0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
              0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
              0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.001546392, 0.008762887, 0.071649485, 0.140206186, 0.330412371,
              0.409793814, 0.480927835, 0.531958763, 0.593298969, 0.644845361, 0.684536082, 0.726804124, 0.76443299, 0.794845361,
              0.817525773, 0.841752577, 0.860824742, 0.863402062, 0.877319588, 0.779896907, 0.838659794, 0.796391753, 0.767010309,
              0.565463918, 0.597938144, 0.589175258, 0.589690722, 0.580412371, 0.698453608, 0.642783505, 0.595876289, 0.506701031,
              0.295876289, 0.271649485, 0.319072165, 0.179896907, 0.074226804, 0.059278351, 0.03556701, 0.02371134, 0.003608247,
              0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
              0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
              0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.001546392, 0.010824742, 0.027835052, 0.059793814, 0.124226804,
              0.214948454, 0.389690722, 0.500515464, 0.555670103, 0.60257732, 0.655154639, 0.686597938, 0.712886598, 0.736597938,
              0.745360825, 0.767010309, 0.78556701, 0.8, 0.811340206, 0.819072165, 0.821134021, 0.823195876, 0.820103093, 0.813917526,
              0.802061856, 0.784536082, 0.752061856, 0.731443299, 0.696907216, 0.667525773, 0.630412371, 0.583505155, 0.532989691,
              0.482989691, 0.426804124, 0.354123711, 0.272164948, 0.17371134, 0.128350515, 0.063402062, 0.008247423, 0.0,
              0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

# run time series simulation
for p in PV_profile:

    # BESS control logic, shave PV peak over 0.5, and discharge when SOC is above 50%
    if p>0.5:
        BESS_p = 0.5-p
    else:
        BESS_p = 0

    if der_list[1].get_bess_soc() > 0.5 and p < 0.5:
        BESS_p = 0.5-p

    ckt_int.update_der_p_pu(p_pu_list=[p, BESS_p])

    ckt_int.der_convergence_process()

    ckt_int.read_line_flow()

    ckt_int.ckt.dss.circuit.set_active_element('line.line2')

    plot_obj.add_to_traces(
        {
            'v': sum(list(ckt_int.ckt.buses.loc['der', ['Vpu_A', 'Vpu_B', 'Vpu_C']]))/3,
        },
        {
            'PV': der_list[0].p_out_pu,
            'BESS': der_list[1].p_out_pu,
            'Total': der_list[0].p_out_pu+der_list[1].p_out_pu,
        },
        {
            'PV': der_list[0].q_out_pu,
            'BESS': der_list[1].q_out_pu,
        },
        {
            'SOC':der_list[1].get_bess_soc()
        }
    )
    # step tsim

    tsim = tsim + delt

plot_obj.prepare()
plot_obj.show()

