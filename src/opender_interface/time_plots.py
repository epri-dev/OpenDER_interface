# Copyright © 2023 Electric Power Research Institute, Inc. All rights reserved.

# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
# · Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
# · Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# · Neither the name of the EPRI nor the names of its contributors may be used
#   to endorse or promote products derived from this software without specific
#   prior written permission.


import sys

import matplotlib.pyplot as plt
import numpy as np
import opender.der
import pandas as pd
import pickle
import matplotlib
import time
from typing import Union, List, Tuple


class TimePlots:
    """
    This class generates a time-series figure for dynamic or quasi-static time series (QSTS) simulation.
    Every time step, the datapoints should be added to the class by self.add_to_traces() method.
    After simulation, the plot is prepared by self.prepare(), ready to be saved or shown.
    """

    def __init__(self, rows: int, cols: int = 1, title: list = None, ylabel: list = None):
        """
        :param rows: Rows of the plots
        :param cols: Columns of the plots
        :param title: Titles of the plots
        :param ylabel: Y-axis labels of the plots
        """
        self.num_of_subplots = rows * cols
        self.rows = rows
        self.cols = cols

        self.title = title
        self.ylabel = ylabel
        self.traces = [[]]
        for i in range(self.num_of_subplots - 1):
            self.traces.append([])

    def add_to_traces(self, *args):
        """
        Add datapoints to the plots. Each subplot should have one dictionary containing its plotted value.
        For example, if a time plot with 2 subplot is initialized, then this method can be invoked as:
        TimePlots.add_to_traces(
        {
            'A':a,
            'B':b,
        },
        {
            'C':c,
        })
        In this case, the first subplot will have two traces 'A' and 'B', and the second subplot will have one trace 'C'

        :param args: Dictionaries containing the datapoints to be plotted
        """
        for i,arg in enumerate(args):
            self.traces[i].append(arg)


    def prepare(self):
        """
        Prepare the time plot
        """
        self.fig, self.axes = plt.subplots(nrows=self.rows, ncols=self.cols, sharex=True)

        if self.num_of_subplots ==1:
            self.axes=[self.axes]
        if self.cols>1:
            self.axes=self.axes.flatten()

        for i in range(self.num_of_subplots):
            self.traces[i]=pd.DataFrame(self.traces[i])

        for i in range(self.num_of_subplots):
            for j,trace in enumerate(self.traces[i]):
                self.axes[i].plot(np.array(range(len(self.traces[i][trace])))*opender.der.DER.t_s, self.traces[i][trace], label=trace)

            try:
                self.axes[i].set_title(self.title[i])
            except:
                pass

            try:
                self.axes[i].set_ylabel(self.ylabel[i])
            except:
                pass

            self.axes[i].grid()

            self.axes[i].legend(loc=2)
        self.axes[-1].set_xlabel('Time (s)')
        # plt.tight_layout()

    def show(self):
        """
        Show plot
        """
        plt.show()

    def save(self, path='fig.svg', datapath=None):
        """
        Save figure. The file extension has to be provided. If datapath is provided, the plot figure will be saved as
        pickle file.

        :param path: Saved figure path. If not provided. a 'fig.svg' file will be saved locally in the same folder
        :param datapath: Saved figure data path
        """

        if datapath is not None:
            with open(datapath, 'wb') as f:  # should be 'wb' rather than 'w'
                pickle.dump(self.traces, f)

        plt.savefig(path)

    def prepare_ani(self):
        """
        Prepare animation.
        """
        print('preparing animations')

        self.fig, self.axes = plt.subplots(nrows=self.rows, ncols=self.cols, sharex=True)

        if self.num_of_subplots ==1:
            self.axes=[self.axes]
        if self.cols>1:
            self.axes=self.axes.flatten()

        from matplotlib.animation import FuncAnimation
        matplotlib.rcParams['animation.ffmpeg_path'] = r'C:\Users\pyma001\Box\_Documents\ffmpeg.exe' # Please install ffmpeg and reference it here.

        for i in range(self.num_of_subplots):
            self.traces[i] = pd.DataFrame(self.traces[i])

        self.lines = [[]]
        for i in range(self.num_of_subplots):
            self.lines.append([])
            for j, trace in enumerate(self.traces[i]):
                self.lines[i].append(self.axes[i].plot([],[], label=trace)[0])
            try:
                self.axes[i].set_title(self.title[i])
            except:
                pass

            try:
                self.axes[i].set_ylabel(self.ylabel[i])
            except:
                pass

            try:
                ymin_tmp = np.min(self.traces[i].values)
                ymax_tmp = np.max(self.traces[i].values)
                ymin = ymin_tmp - (ymax_tmp-ymin_tmp)*0.1
                ymax = ymax_tmp + (ymax_tmp-ymin_tmp)*0.1
                if ymin==ymax:
                    ymin=ymin-0.1
                    ymax=ymax+0.1

            except ValueError:
                ymin = -0.1
                ymax = 1.1
            self.axes[i].set_ylim(ymin,ymax)
            self.axes[i].set_xlim(0,len(self.traces[i][trace]) * opender.der.DER.t_s)
            print(f'ylim={ymax},{ymin}')

            self.axes[i].grid(visible=True)

            self.axes[i].legend()

        self.axes[-1].set_xlabel('Time (s)')
        # plt.tight_layout()
        self.ani = FuncAnimation(self.fig, self.animate, interval=100, blit=True,save_count=int(len(self.traces[0])*1.1))

    def animate(self,ii):
        """
        Animation function to be executed every animation frame
        """
        for i in range(self.num_of_subplots):
            for j, trace in enumerate(self.traces[i]):
                x=np.array(range(len(self.traces[i][trace])))[0:ii] * opender.der.DER.t_s
                y=self.traces[i][trace].values[0:ii]

                self.lines[i][j].set_data(x,y)

        # plt.gcf().text(0.1, 0, 'asdfasdf', fontsize=14)
        return [item for sublist in self.lines for item in sublist]

    def save_ani(self,path='fig.mp4'):
        """
        Save animation to a mp4 file.

        :param path: Saved mp4 animation path. If not provided, default as 'fig.mp4' in the same folder
        """
        print(f'Saving animations to {path}', end=' ')
        start = time.perf_counter()
        self.ani.save(path, fps=25, extra_args=['-vcodec', 'libx264'])
        print(f"... Completed in {time.perf_counter()-start:.1f}s")


class CombinedTimePlots(TimePlots):
    """
    This class is used to create a time-series figure to contain multiple simulation results.
    """
    def __init__(self, rows: int, cols: int = 1, title: list = None, ylabel: list = None):
        """
        :param rows: Rows of the plots
        :param cols: Columns of the plots
        :param title: Titles of the plots
        :param ylabel: Y-axis labels of the plots
        """
        super().__init__(rows, cols, title, ylabel)

    def combine_time_plots(self, tplot_list: List[TimePlots] = None, traces_list: List[pd.DataFrame] = None):
        """
        :param tplot_list: List of TimePlots objects
        """
        if tplot_list is not None:
            for tplot in tplot_list:
                for i in range(self.num_of_subplots):
                    tplot.traces[i] = pd.DataFrame(tplot.traces[i])

            for i in range(self.num_of_subplots):
                self.traces[i] = pd.concat([tplot.traces[i] for tplot in tplot_list], axis=1)

        if traces_list is not None:
            # for i in range(self.num_of_subplots):
            #     self.traces[i] = traces_list[i]

            for i in range(self.num_of_subplots):
                self.traces[i] = pd.concat([traces[i] for traces in traces_list], axis=1)