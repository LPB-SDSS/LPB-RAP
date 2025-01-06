"""LAFORET-PLUC-BE-RAP/SFM - targeted net forest map
Sonja Holler (SH), Melvin Lippe (ML) and Daniel Kuebler (DK), 
2021 Q2/Q3 
(Re-)written according to PEP 8 and modified original model. 
Based on:

Make an MP4 file of the output of the LUC model of Mozambique
Judith Verstegen, 2017-07-04"""

from matplotlib import animation
from matplotlib import colors as cls
from matplotlib import pyplot as plt
from matplotlib import colors as mcolors
from matplotlib.font_manager import FontProperties
import matplotlib.cm
plt.switch_backend('agg')
import numpy as np
import matplotlib as mpl
colormap = mpl.colormaps['viridis'].resampled(5)
from pcraster import *
import Parameters
import Filepaths
import ast
import json
# get the filename for the output:
import sys
import os
filename = os.path.splitext(os.path.basename(sys.argv[0]))[0]
filename = str(filename)

# # get the dictionary
targeted_net_forest_dictionary = json.loads(sys.argv[1])

net_forest_initial_area = targeted_net_forest_dictionary['initial_area']
net_forest_targeted_percentage_increment = targeted_net_forest_dictionary['targeted_percentage_increment']
net_forest_targeted_area_increment = targeted_net_forest_dictionary['targeted_area_increment']
net_forest_targeted_area_total = targeted_net_forest_dictionary['targeted_total_area']

##############
### inputs ###
##############

## SH: LPB alternation
timesteps = 1
init_year = Parameters.get_initial_simulation_year()
country = Parameters.get_country()
region = Parameters.get_region()
baseline_scenario = Parameters.get_model_baseline_scenario()
model_scenario = Parameters.get_model_scenario()
fn = 'RAP_tnf'

## SH: LPB alternation
list_all_colors = {0:'white',
                   1: 'black',
                   2: colormap(2),
                   3: colormap(5),
                   }

list_all_names = {1:'= region',
                   2:'= existing net forest according to national map',
                   3:'= simulated required additional net forest area',
                   }

## SH: LPB alternation
legend_loc = (0.975,0.175)  # Esmeraldas right bottom

############
### MAIN ###
############

## SH: LPB alternation
# SH: look up the files in the according new output folder
wd = os.getcwd()
# open the raster and read out the data in a numpy array
# open the raster and read out the data in a numpy array
if (8 - len(fn)) > 0: nr_zeros = 8 - len(fn)
else:  nr_zeros = 0
in_fn = os.path.join(wd, Filepaths.folder_RAP_targeted_net_forest, fn + nr_zeros * '0' + '.001')
setclone(in_fn)
amap = readmap(in_fn)
data = pcr2numpy(amap, 0)

# create custom color map
colorlist = []

valuelist = list(list_all_names.keys())
for i in range(0, len(valuelist)):
    valuelist[i] = int(valuelist[i])
maxvalue = np.max(valuelist)
intmaxvalue = maxvalue.item()
for i in range(0, intmaxvalue + 1):
    if i in list_all_colors:
        colorlist.append(list_all_colors.get(i))     
    else:
        colorlist.append('None')

# create the figure
f, axarr = plt.subplots(1)
plt.axis('off')
# making color map and normalization scheme
cmap_long = cls.ListedColormap(colorlist, name='long')
norm_without_mv = cls.Normalize(vmin=0, \
                    vmax = intmaxvalue)
# create the legend
p = []
s = []

## SH: LPB alternation
# JV: loop over reversed list for ascending order
for nr in list_all_names.keys():#[::-1]:
  p.append(plt.Circle((0, 0), radius=3, lw=0, fc=list_all_colors[nr]))
  s.append(list_all_names[nr])
leg = axarr.legend(p, s, loc='right', bbox_to_anchor=legend_loc,\
                   prop={'size':4}, ncol=1, fancybox=True,\
                   borderpad=0.2, bbox_transform=f.transFigure)
title = axarr.text(-0.2, 1.05, '', weight='semibold', transform=axarr.transAxes)
title_annotation = axarr.text(-0.2, 1, '', fontstyle='italic', transform=axarr.transAxes)
subtitle = axarr.text(-0.2, 0.95, '', transform=axarr.transAxes)
year = axarr.text(-0.2, 0.85, '', transform=axarr.transAxes)

initial_area = axarr.text(-0.2, 0.75, '', transform=axarr.transAxes, size=6)
targeted_percentage = axarr.text(-0.2, 0.70, '', transform=axarr.transAxes, size=6)
targeted_additional_area = axarr.text(-0.2, 0.67, '', transform=axarr.transAxes, size=6)
targeted_total_area = axarr.text(-0.2, 0.64, '', transform=axarr.transAxes, size=6)

## SH: LPB alternation
# JV: use imshow to plot the raster over time in two functions for the animation
def init():
    im = axarr.imshow(data, norm=norm_without_mv, zorder=0,\
                            cmap=cmap_long, animated=True, interpolation='nearest')
    return im, leg, year, subtitle, title_annotation, title

## SH: LPB alternation
def animate(i):
    t = i + 1
    # if t < 10:
    #     fn = in_fn[:-3] + '00' + str(t)
    # else:
    #     fn = in_fn[:-3] + '0' + str(t)
    ##print fn
    amap = readmap(in_fn)
    data = pcr2numpy(amap, 0)
    im = axarr.imshow(data, norm=norm_without_mv, zorder=0,\
                            cmap=cmap_long, animated=True, interpolation='nearest')
    targeted_total_area.set_text('targeted total area: ' + str(net_forest_targeted_area_total))
    targeted_additional_area.set_text('targeted additional area: ' + str(net_forest_targeted_area_increment))
    targeted_percentage.set_text('targeted percentage increment: ' + str(net_forest_targeted_percentage_increment))
    initial_area.set_text('initial net forest area: ' + str(net_forest_initial_area))
    year.set_text('Year = ' + str(init_year + t - 1))
    subtitle.set_text(country + ' ' + region + ' ' + baseline_scenario + ' ' + model_scenario + '-scenario')
    title_annotation.set_text(' - most suitable area simulated to achieve net forest area target')
    title.set_text('RAP LULCC SIMULATION - targeted net forest area simulated')
    return im, leg, year, subtitle, title_annotation, title

im_ani = animation.FuncAnimation(f, animate, interval=300, \
                                   blit=False, frames = timesteps,\
                                   init_func=init)
im_ani.save(os.path.join(Filepaths.folder_RAP_GIFs, filename +'_' + country +'_' + region + '_' + model_scenario +'_scenario_VA.gif'), dpi=300, metadata={'artists':'Judith Verstegen & Sonja Holler'})
# ValueError: unknown file extension: .mp4
#plt.show()

