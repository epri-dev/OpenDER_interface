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
# from opender import DER, DER_PV, DER_BESS
from opender_interface import TimePlots
from conftest import showplt


class TestTimePlot:
    def test_time_plot(self):
        timeplot = TimePlots(2,1,['1','2'],['4','5'])

        for i in range(50):
            timeplot.add_to_traces(
                {
                    'A':i,
                    'B':i-1,
                },
                {
                    'c':i*10
                }
            )
        timeplot.prepare()
        if showplt:
            timeplot.show()

    def test_time_plot_animation(self):
        timeplot = TimePlots(2,1,['1','2'],['4','5'])

        for i in range(10):
            timeplot.add_to_traces(
                {
                    'A':i,
                    'B':i-1,
                },
                {
                    'c':i*10
                }
            )
        timeplot.prepare_ani()
        if showplt:
            timeplot.show()
