"""LAFORET-PLUC-BE-RAP/SFM - LPB_movie_land_use
Sonja Holler (SH), Melvin Lippe (ML) and Daniel Kuebler (DK),
2021 Q2/Q3
(Re-)written according to PEP 8 and modified original model.
Based on:

Make an MP4 file of the output of the LUC model of Mozambique
Judith Verstegen, 2017-07-04"""
import matplotlib.cm
from matplotlib import animation
from matplotlib import colors as cls
from matplotlib import pyplot as plt
from matplotlib import colors as mcolors
from matplotlib.font_manager import FontProperties
plt.switch_backend('agg')
import matplotlib as mpl
colormap = mpl.colormaps['viridis']
import numpy as np
from pcraster import *
import Parameters
import Filepaths
# get the filename for the output:
import sys
import os
filename = os.path.splitext(os.path.basename(sys.argv[0]))[0]
filename = str(filename)

##############
### inputs ###
##############

if Parameters.get_mplc_with_maximum_anthropogenic_impact_simulation_decision() == True:
    anthropogenic_impact_simulation = '* simulation conducted WITH additional allocation for depiction of maximum anthropogenic impact'
else:
    anthropogenic_impact_simulation = '* simulation conducted WITHOUT additional allocation for depiction of maximum anthropogenic impact'



## SH: LPB alternation
timesteps = Parameters.get_number_of_time_steps()
init_year = Parameters.get_initial_simulation_year()
country = Parameters.get_country()
region = Parameters.get_region()
baseline_scenario = Parameters.get_model_baseline_scenario()
model_scenario = Parameters.get_model_scenario()
fn = 'mplctfpr'

# classify the values in 7 classes:
# class 1 = 0 %
# class 2 = >0 to 20 %
# class 3 = >20 to 40 %
# class 4 = >40 to 60 %
# class 5 = >60 to 80 %
# class 6 = >80 to <100 %
# class 7 = 100 %

## SH: LPB alternation
# working solution 1 with colormap viridis
list_all_colors = {0:'white',
                   1: colormap(0.1),
                   2: colormap(0.2),
                   3: colormap(0.4),
                   4: colormap(0.6),
                   5: colormap(0.8),
                   6: colormap(0.9),
                   7: colormap(1.0),
                   8: 'black'}

list_all_names = {1:'1 = 0 % probability',
                   2:'2 = >0 to 20 % probability',
                   3:'3 = >20 to 40 % probability',
                   4:'4 = >40 to 60 % probability',
                   5:'5 = >60 to 80 % probability',
                   6:'6 = >80 to <100 % probability',
                   7:'7 = 100 % probability',
                   8:'8 = remaining region'}

## SH: LPB alternation
legend_loc = (0.975,0.175)  # Esmeraldas right bottom

############
### MAIN ###
############

## SH: LPB alternation
# SH: look up the files in the according new output folder
# open the raster and read out the data in a numpy array
if (8 - len(fn)) > 0: nr_zeros = 8 - len(fn)
else:  nr_zeros = 0
in_fn = os.path.join(Filepaths.folder_FOREST_PROBABILITY_MAPS_fud_mplc_probabilities_classified,  fn + nr_zeros * '0' + '.001')
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

anthropogenic_impact = axarr.text(-0.2, -0.1, '', size=6, transform=axarr.transAxes)

## SH: LPB alternation
# JV: use imshow to plot the raster over time in two functions for the animation
def init():
    im = axarr.imshow(data, norm=norm_without_mv, zorder=0,\
                            cmap=cmap_long, animated=True, interpolation='nearest')
    return im, leg, year, subtitle, title_annotation, title

## SH: LPB alternation
def animate(i):
    t = i + 1
    if t < 10:
        fn = in_fn[:-3] + '00' + str(t)
    else:
        fn = in_fn[:-3] + '0' + str(t)
    amap = readmap(fn)
    data = pcr2numpy(amap, 0)
    im = axarr.imshow(data, norm=norm_without_mv, zorder=0,\
                            cmap=cmap_long, animated=True, interpolation='nearest')

    anthropogenic_impact.set_text(anthropogenic_impact_simulation)

    year.set_text('Year = ' + str(init_year + t - 1))
    subtitle.set_text(country + ' ' + region + ' ' + baseline_scenario + ' ' + model_scenario + '-scenario')
    title_annotation.set_text(' - forest disturbed/undisturbed in net/gross forest probabilities classified')
    title.set_text('LPB LULCC SIMULATION - most probable landscape configuration')
    return im, leg, year, subtitle, title_annotation, title

im_ani = animation.FuncAnimation(f, animate, interval=300, \
                                   blit=False, frames = timesteps,\
                                   init_func=init)
im_ani.save(os.path.join(Filepaths.folder_GIFs, filename +'_' + country +'_' + region + '_' + model_scenario +'_scenario.gif'), dpi=300, metadata={'artists':'Judith Verstegen & Sonja Holler'})
# ValueError: unknown file extension: .mp4
#plt.show()

