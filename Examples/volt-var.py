import numpy as np
import opender
from opender_interface.time_plots import TimePlots
from opender_interface.xy_plot import XYPlots

'''
This is an illustrative example showcasing the functionality of the plot class, demonstrating its ability to present the
DER information and status.
'''

## voltage profile
V_ss = [1, 1.03, 0.93, 1.09, 1, 0.97, 1.07, 0.91, 1]
V = np.concatenate([[v]*30 for v in V_ss])


t_s = opender.DER.t_s = 1

## create DER object
der_obj = opender.DER_BESS()
der_obj.der_file.QV_MODE_ENABLE = True
der_obj.der_file.QV_OLRT = 5

## plot object
tplot = TimePlots(3,1, ['Voltage [pu]', 'Power output [pu]', 'Reactive power output [pu]'])
xyplot = XYPlots(der_obj,pu=False)

capture = range(20, 400, 30)

## DER simulation
for i, V in enumerate(V):
    der_obj.update_der_input(v_pu=float(V), f=60, p_dem_pu=1)
    der_obj.run()

    tplot.add_to_traces(
        {

            'V': V,
            # 'V': V/240
        },
        {
            'OpenDER P': der_obj.p_out_pu,
        },
        {
            'OpenDER Q': der_obj.q_out_pu,
        },
    )
    if i>capture[0]:
        xyplot.add_point_to_plot(der_obj)
        capture = capture[1:]

## plot simulation result
tplot.prepare()
for ax in tplot.axes:
    ax.grid()

tplot.fig.set_size_inches(10,6)
# tplot.save('1.svg')
tplot.show()

xyplot.prepare_vq_plot()
xyplot.prepare_pq_plot()
# xyplot.save_fig('2')
xyplot.show()
