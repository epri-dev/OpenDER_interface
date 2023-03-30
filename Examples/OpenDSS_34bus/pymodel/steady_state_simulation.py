import matplotlib.pyplot as plt
import pathlib
import os
from opender_interface.opendss_interface import OpenDSSInterface
from opender_interface.opender_interface import DERModelInterface


#%%
script_path = pathlib.Path(os.path.dirname(__file__))
circuit_folder = script_path.parents[0].joinpath("IEEE_34Bus")
dss_file = circuit_folder.joinpath("ieee34Mod2_der.dss")
load_file = script_path.joinpath("load_profile.xlsx")

# folder and files
home_folder = script_path.parents[0]
save_folder = home_folder.joinpath("sim_data")


# TODO convert this to interface to generate topology automatically
topology = [
    [802, 806],
    [806, 808],
    [808, 810],
    [808, 812],
    [812, 814],
    [814, 850],
    [850, 816],
    [816, 818],
    [818, 820],
    [820, 822],
    [816, 824],
    [824, 826],
    [824, 828],
    [828, 830],
    [830, 854],
    [854, 856],
    [854, 852],
    [852, 832],
    [832, 888],
    [888, 890],
    [832, 858],
    [858, 864],
    [858, 834],
    [834, 842],
    [842, 844],
    [844, 846],
    [846, 848],
    [860, 836],
    [836, 840],
    [836, 862],
    [862, 838]
]
# compile circuit, add an energy meter, solve, and import bus coordinate
# this will force opendss to generate bus distance information
cmd_list = [
    'new energymeter.Meter element=line.L1 terminal=1',
    'solve',
    'Buscoords IEEE34_BusXY.csv',
    ]

fdr = OpenDSSInterface(str(dss_file))
fdr.cmd(cmd_list)


fdr.initialize()
fdr.init_PVSystems()


def plot_voltage_profile(ax, data_label, data_color):
    for line in topology:
        ax.plot([fdr.buses['distance'].loc[str(line[0])],
                 fdr.buses['distance'].loc[str(line[1])]],
                [fdr.buses[data_label].loc[str(line[0])],
                 fdr.buses[data_label].loc[str(line[1])]], color=data_color)

    ax.scatter(fdr.buses['distance'], fdr.buses[data_label], label=data_label, color=data_color)


scale = 1
for i, PV in fdr.DERs.iterrows():
    name = PV['name']
    fdr.cmd(f'PVSystem.{name}.%Pmpp={scale*100}')

fdr.enable_control()
fdr.solve_power_flow()
fdr.read_sys_voltage()

fig, ax = plt.subplots(2, 1,figsize=(10,5))

plot_voltage_profile(ax[0],'Vpu_A','blue')
plot_voltage_profile(ax[0],'Vpu_B','orange')
plot_voltage_profile(ax[0],'Vpu_C','green')

ax[0].set_xlabel('Distance (miles)')
ax[0].set_ylabel('Voltage (pu)')
ax[0].set_ylim(0.9, 1.09)
ax[0].grid(visible=True)
ax[0].legend(loc=2)
ax[0].set_title('OpenDSS')



#%%
# connect a DER to each bus
der_interface = fdr.create_opender_objs(p_dc_pu=scale,
                                   CONST_PF_MODE_ENABLE=True,
                                   CONST_PF=0.9,
                                   CONST_PF_EXCITATION='ABS')


# run a load flow and check the feeder total power

der_interface.der_convergence_process()

#################

plot_voltage_profile(ax[1],'Vpu_A','blue')
plot_voltage_profile(ax[1],'Vpu_B','orange')
plot_voltage_profile(ax[1],'Vpu_C','green')

ax[1].set_xlabel('Distance (miles)')
ax[1].set_ylabel('Voltage (pu)')
ax[1].set_ylim(0.9, 1.09)
ax[1].grid(visible=True)
ax[1].legend(loc=2)
ax[1].set_title('OpenDSS + OpenDER')

fig.tight_layout()
fig.savefig(f'node_voltage.svg')
plt.show()


