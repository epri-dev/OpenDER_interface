import numpy as np
import opender
from opender_interface.time_plots import TimePlots
from opender_interface.xy_plot import XYPlots

'''
This example demonstrates the plotting capability of the OpenDER model interface.
'''

# create voltage profile for plotting.
V_ss = [1, 1.03, 0.93, 1.09, 1, 0.97, 1.07, 0.91, 1]
V = np.concatenate([[v]*30 for v in V_ss])
t_s = opender.DER.t_s = 1

# create DER object, and enable Volt-var function
der_obj = opender.DER_BESS()
der_obj.der_file.QV_MODE_ENABLE = True
der_obj.der_file.QV_OLRT = 5

# Create time-series plot object (tplot). It has 3 rows and 1 columns. The subplot titles are configured
tplot = TimePlots(3,1, ['Voltage [pu]', 'Power output [pu]', 'Reactive power output [pu]'])
# Create steady-state chart object (xyplot)
xyplot = XYPlots(der_obj,pu=False)

# save a data point on steady-state chart once per 30 seconds
capture = range(20, 400, 30)

# Dynamic simulation and save data points
for i, V in enumerate(V):
    der_obj.update_der_input(v_pu=float(V), f=60, p_dem_pu=1)
    der_obj.run()

    # Save voltage, DER output P and Q to time-series plot
    tplot.add_to_traces(
        {
            'V': V,
        },
        {
            'OpenDER P': der_obj.p_out_pu,
        },
        {
            'OpenDER Q': der_obj.q_out_pu,
        },
    )

    # Every 30 seconds, save a datapoint to the steady-state plot
    if i>capture[0]:
        xyplot.add_point_to_plot(der_obj)
        capture = capture[1:]

# plot simulation result
tplot.prepare()
for ax in tplot.axes:
    ax.grid()

tplot.fig.set_size_inches(10,6)
tplot.show()

xyplot.prepare_vq_plot()
xyplot.prepare_pq_plot()
xyplot.show()
