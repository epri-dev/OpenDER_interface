import matplotlib.pyplot as plt
import pathlib
import os
from opender_interface.opendss_interface import OpenDSSInterface
from opender_interface.der_interface import DERInterface
from opender import DERCommonFileFormat

'''
This is an example comparing the system voltage profile and load flow with and without DER
'''

# circuit path
script_path = pathlib.Path(os.path.dirname(__file__))
circuit_folder = script_path.parents[0].joinpath("IEEE_34Bus")
dss_file = circuit_folder.joinpath("ieee34Mod2_der.dss")
load_file = script_path.joinpath("load_profile.xlsx")


# create OpenDER interface
ckt = OpenDSSInterface(str(dss_file))
ckt_int = DERInterface(ckt)

# initialize circuit
ckt_int.initialize(DER_sim_type='PVSystem')

# This function plots voltage profile for a specific phase.
def plot_voltage_profile(ax, data_label, data_color):

    # Lines
    for _, line in ckt_int.ckt.lines.iterrows():
        ax.plot([ckt_int.ckt.buses['distance'].loc[str(line['bus1']).split('.')[0]],
                 ckt_int.ckt.buses['distance'].loc[str(line['bus2']).split('.')[0]]],
                [ckt_int.ckt.buses[data_label].loc[str(line['bus1']).split('.')[0]],
                 ckt_int.ckt.buses[data_label].loc[str(line['bus2']).split('.')[0]]], color=data_color)

    # Transformers
    ax.plot([ckt_int.ckt.buses['distance'].loc['814'],
             ckt_int.ckt.buses['distance'].loc['814r']],
            [ckt_int.ckt.buses[data_label].loc['814'],
             ckt_int.ckt.buses[data_label].loc['814r']], color=data_color)
    ax.plot([ckt_int.ckt.buses['distance'].loc['852'],
             ckt_int.ckt.buses['distance'].loc['852r']],
            [ckt_int.ckt.buses[data_label].loc['852'],
             ckt_int.ckt.buses[data_label].loc['852r']], color=data_color)
    ax.plot([ckt_int.ckt.buses['distance'].loc['832'],
             ckt_int.ckt.buses['distance'].loc['888']],
            [ckt_int.ckt.buses[data_label].loc['832'],
             ckt_int.ckt.buses[data_label].loc['888']], color=data_color)

    # Bus voltages
    ax.scatter(ckt_int.ckt.buses['distance'], ckt_int.ckt.buses[data_label], label=data_label, color=data_color)


# This function plots power flow profile for a specific phase.
def plot_power_profile(ax, data_label, data_color):
    # Lines
    i=0
    for index, line in ckt_int.ckt.lines.iterrows():

        if abs(line.loc[data_label].real)>0.1:
            ax.scatter((ckt_int.ckt.buses['distance'].loc[str(line['bus1'].split('.')[0])]+ckt_int.ckt.buses['distance'].loc[str(line['bus2']).split('.')[0]])/2,
                       line.loc[data_label].real, color=data_color)

            for j in range(i,len(ckt_int.ckt.lines)):
                line2 = ckt_int.ckt.lines.iloc[j]
                if abs(line2.loc[data_label].real) > 0.1:
                    if line['bus1'] == line2['bus2'] or line['bus2'] == line2['bus1'] or\
                       (i==7 and j==8) or (i==39 and j==40) or (i==39 and j==50):
                        ax.plot([(ckt_int.ckt.buses['distance'].loc[str(line['bus1'].split('.')[0])] + ckt_int.ckt.buses['distance'].loc[str(line['bus2']).split('.')[0]]) / 2,
                                 (ckt_int.ckt.buses['distance'].loc[str(line2['bus1'].split('.')[0])] + ckt_int.ckt.buses['distance'].loc[str(line2['bus2']).split('.')[0]]) / 2],
                                [line.loc[data_label].real, line2.loc[data_label].real],color=data_color)
        i=i+1


# create an OpenDER object to each PVSystem in DSS circuit
der_file = DERCommonFileFormat(NP_VA_MAX=300000,
                               NP_P_MAX=300000,
                               NP_Q_MAX_INJ=300000,
                               NP_Q_MAX_ABS=300000,
                               CONST_PF_MODE_ENABLE=True,
                               CONST_PF=0.9,
                               CONST_PF_EXCITATION='ABS')
der_list = ckt_int.create_opender_objs(der_file, p_pu=1)

# run a load flow and check the feeder total power
ckt_int.der_convergence_process()
ckt_int.read_sys_voltage()
ckt_int.read_line_flow()

fig, ax = plt.subplots(2, 2,figsize=(10,5),sharex=True)
ax = [ax[0][0], ax[0][1], ax[1][0], ax[1][1]]
plot_voltage_profile(ax[0],'Vpu_A','blue')
plot_voltage_profile(ax[0],'Vpu_B','orange')
plot_voltage_profile(ax[0],'Vpu_C','green')

ax[0].set_xlabel('Distance (miles)')
ax[0].set_ylabel('Voltage (pu)')
ax[0].set_ylim(0.9, 1.09)
ax[0].grid(visible=True)
ax[0].legend(loc=2)
ax[0].set_title('P=1')

plot_power_profile(ax[2],'flowS_A','blue')
plot_power_profile(ax[2],'flowS_B','orange')
plot_power_profile(ax[2],'flowS_C','green')

ax[2].set_xlabel('Distance (miles)')
ax[2].set_ylabel('Power (kW)')
# ax[2].set_ylim(0.9, 1.09)
ax[2].grid(visible=True)
ax[2].legend(loc=2)
ax[2].set_title('P=1')


# update DER output powers to 0
ckt_int.update_der_p_pu([0,0,0,0,0])
# run a load flow and check the feeder total power
ckt_int.der_convergence_process()
ckt_int.read_sys_voltage()
ckt_int.read_line_flow()


plot_voltage_profile(ax[1],'Vpu_A','blue')
plot_voltage_profile(ax[1],'Vpu_B','orange')
plot_voltage_profile(ax[1],'Vpu_C','green')

ax[1].set_xlabel('Distance (miles)')
ax[1].set_ylabel('Voltage (pu)')
ax[1].set_ylim(0.9, 1.09)
ax[1].grid(visible=True)
ax[1].legend(loc=2)
ax[1].set_title('P=0')

plot_power_profile(ax[3],'flowS_A','blue')
plot_power_profile(ax[3],'flowS_B','orange')
plot_power_profile(ax[3],'flowS_C','green')

ax[3].set_xlabel('Distance (miles)')
ax[3].set_ylabel('Power (kW)')
# ax[2].set_ylim(0.9, 1.09)
ax[3].grid(visible=True)
ax[3].legend(loc=2)
ax[3].set_title('P=0')

fig.tight_layout()
fig.savefig(f'node_voltage.svg')
plt.show()


