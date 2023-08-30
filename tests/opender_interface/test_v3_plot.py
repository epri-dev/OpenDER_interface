"""
Copyright © 2023 Electric Power Research Institute, Inc. All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:
· Redistributions of source code must retain the above copyright notice,
  this list of conditions and the following disclaimer.
· Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.
· Neither the name of the EPRI nor the names of its contributors may be used
  to endorse or promote products derived from this software without specific
  prior written permission.
"""

import pytest
from opender import DER, DER_PV, DER_BESS
from opender_interface import XYPlots
from conftest import showplt

class TestXYPlot:

    def test_xy_plot(self):
        der_obj = DER_PV()
        der_obj.der_file.OV1_TRIP_V = 3
        der_obj.der_file.OV2_TRIP_V = 3
        der_obj.der_file.UV1_TRIP_V = 0
        der_obj.der_file.UV1_TRIP_V = 0

        xyplot = XYPlots(der_obj)

        der_obj.update_der_input(p_dc_pu=1,v_pu=[1,0.5,0.8], theta=[0, 2, 4])
        der_obj.run()

        xyplot.add_point_to_plot()
        xyplot.prepare_v3_plot(l2l=True)

        if showplt:
            xyplot.show()

        xyplot.prepare_v3_plot(v_vector=[1,0.8, 0.5,0,2,4])

        if showplt:
            xyplot.show()