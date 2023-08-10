import sys

import matplotlib.pyplot as plt
import numpy as np
import opender.der
import pandas as pd
import pickle
from matplotlib.animation import FuncAnimation
import matplotlib
import time

# region This parameter is configured for animation. If you intend to utilize this function, please uncomment this command line and set the appropriate path accordingly.
# matplotlib.rcParams['animation.ffmpeg_path'] = r'C:\Users\pyma001\Box\_Documents\ffmpeg.exe'
# endregion



'''
This is the plot class utilized for creating figures depicting DER operation information over a timeline. 
'''
class TimePlots:

    '''
    Initialization, The input parameters "rows" and "cols" dictate the arrangement of subplots.
    '''
    def __init__(self, rows: int, cols: int = 1, title: list = None, ylabel: list = None):
        self.num_of_inputs = rows*cols
        self.fig, self.axes = plt.subplots(nrows=rows, ncols=cols, sharex=True)

        if self.num_of_inputs ==1:
            self.axes=[self.axes]
        if cols>1:
            self.axes=self.axes.flatten()

        self.title = title
        self.ylabel = ylabel
        self.traces = [[]]
        for i in range(self.num_of_inputs-1):
            self.traces.append([])

    '''
    Add trace (traces) to be plotted 
    '''
    def add_to_traces(self, *args):
        for i,arg in enumerate(args):
            self.traces[i].append(arg)

    '''
    Plot traces of each subplot
    '''
    def prepare(self):
        for i in range(self.num_of_inputs):
            self.traces[i]=pd.DataFrame(self.traces[i])


        for i in range(self.num_of_inputs):
            for j,trace in enumerate(self.traces[i]):
                self.axes[i].plot(np.array(range(len(self.traces[i][trace])))*opender.der.DER.t_s,self.traces[i][trace],label=trace)
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
        plt.tight_layout()

    '''
    Show plot
    '''
    def show(self):
        plt.show()

    '''
    Save figure as svg file.
    Input parameters:
        path: figure name
        datapath: the file used for save trace date  
    '''
    def save(self, path='fig.svg', datapath=None):
        if datapath is not None:
            with open(datapath, 'wb') as f:  # should be 'wb' rather than 'w'
                pickle.dump(self.traces, f)

        plt.savefig(path)


    # region This region is used for animation
    def prepare_ani(self):


        print('preparing animations')
        for i in range(self.num_of_inputs):
            self.traces[i] = pd.DataFrame(self.traces[i])

        self.lines = [[]]
        for i in range(self.num_of_inputs):
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
        plt.tight_layout()
        self.ani = FuncAnimation(self.fig, self.animate, interval=100, blit=True,save_count=int(len(self.traces[0])*1.1))


    def animate(self,ii):
        for i in range(self.num_of_inputs):
            for j, trace in enumerate(self.traces[i]):
                x=np.array(range(len(self.traces[i][trace])))[0:ii] * opender.der.DER.t_s
                y=self.traces[i][trace].values[0:ii]

                self.lines[i][j].set_data(x,y)

        # plt.gcf().text(0.1, 0, 'asdfasdf', fontsize=14)
        return [item for sublist in self.lines for item in sublist]



    def save_ani(self,path='fig.mp4'):
        print(f'Saving animations to {path}', end=' ')
        start = time.perf_counter()
        self.ani.save(path, fps=25, extra_args=['-vcodec', 'libx264'])
        print(f"... Completed in {time.perf_counter()-start:.1f}s")
    # endregion



# if __name__ == "__main__":
#     A=TimePlots(2,2,['a'],['a'])
#
#     for i in range(50):
#         A.add_to_traces({'a':i,'e':i*2},{'b':i},{'c':i})#,{'d':i})
#
#     A.prepare()
#     A.axes[1].get_legend().remove()
#     A.axes[2].get_legend().remove()
#     A.axes[3].get_legend().remove()
#     A.show()