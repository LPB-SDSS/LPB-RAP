"""LAFORET-PLUC-BE-RAP/SFM - LPB mplc forest undisturbed and disturbed net and gross forest
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
colormap = mpl.colormaps['viridis'].resampled(5)
import numpy as np
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
dictionary_of_undisturbed_forest = json.loads(sys.argv[1])

undisturbed_forest_succession_age = dictionary_of_undisturbed_forest['succession_age']
list_of_undisturbed_forest_maptotals = dictionary_of_undisturbed_forest['maptotal_undisturbed_forest']
list_of_new_undisturbed_forest_maptotals = dictionary_of_undisturbed_forest['maptotal_new_undisturbed_forest']



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
fn = 'mplcuduf'

## SH: LPB alternation
# GIF classes
# 1 = region (black), 2 = gross forest(grey), 3 = net forest based on probability(yellow), 4 = mplc net forest disturbed(petrol), 5 = mplc net forest undisturbed(green)
list_all_colors = {0:'white',
                   1: 'black',
                   2: colormap(2),
                   3: colormap(5)}

list_all_names = {1:' = region',
                   2:' = remaining undisturbed forest',
                   3:' = new undisturbed forest'}

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
in_fn = os.path.join(Filepaths.folder_undisturbed_forest_mplc,  fn + nr_zeros * '0' + '.001')
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
print(f'Maxvalue: {intmaxvalue}')
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

user_defined_succession_age = axarr.text(-0.25, 0.8, '', transform=axarr.transAxes, size=5)
maptotal_undisturbed_forest = axarr.text(-0.25, 0.77, '', transform=axarr.transAxes, size=5)
maptotal_new_undisturbed_forest = axarr.text(-0.25, 0.74, '', transform=axarr.transAxes, size=5)




## SH: LPB alternation
# JV: use imshow to plot the raster over time in two functions for the animation
def init():
    im = axarr.imshow(data, norm=norm_without_mv, zorder=0, cmap=cmap_long, animated=True, interpolation='nearest')
    #im = axarr.imshow(data, zorder=0, cmap=cmap_long, animated=True, interpolation='nearest')
    return im, leg, maptotal_new_undisturbed_forest, maptotal_undisturbed_forest,user_defined_succession_age, year, subtitle, title_annotation, title


## SH: LPB alternation
def animate(i):
    number_of_undisturbed_pixels = list_of_undisturbed_forest_maptotals[i]
    number_of_new_undisturbed_pixels = list_of_new_undisturbed_forest_maptotals[i]
    t = i + 1
    if t < 10:
        fn = in_fn[:-3] + '00' + str(t)
    else:
        fn = in_fn[:-3] + '0' + str(t)
    amap = readmap(fn)
    data = pcr2numpy(amap, 0)
    # Test
    unique, counts = np.unique(data, return_counts=True)
    print(f'Time step: {str(init_year + t - 1)}')
    print(np.asarray((unique, counts)).T)
    im = axarr.imshow(data, norm=norm_without_mv, zorder=0, cmap=cmap_long, animated=True, interpolation='nearest')
    #im = axarr.imshow(data, zorder=0, cmap=cmap_long, animated=True, interpolation='nearest')

    maptotal_new_undisturbed_forest.set_text('New undisturbed forest pixels: ' + str(number_of_new_undisturbed_pixels))
    maptotal_undisturbed_forest.set_text('Total undisturbed forest pixels: ' + str(number_of_undisturbed_pixels))
    user_defined_succession_age.set_text('User-defined succession age to undisturbed forest: ' + str(undisturbed_forest_succession_age))
    year.set_text('Year = ' + str(init_year + t - 1))
    subtitle.set_text(country + ' ' + region + ' ' + baseline_scenario + ' ' + model_scenario + '-scenario')
    title_annotation.set_text(' - mplc approximation of remaining and new undisturbed forest by user user setting')
    title.set_text('LPB LULCC SIMULATION - most probable landscape configuration')
    return im, leg, maptotal_new_undisturbed_forest, maptotal_undisturbed_forest, user_defined_succession_age, year, subtitle, title_annotation, title


im_ani = animation.FuncAnimation(f, animate, interval=300, \
                                   blit=False, frames = timesteps,\
                                   init_func=init)
im_ani.save(os.path.join(Filepaths.folder_GIFs, filename +'_' + country +'_' + region + '_' + model_scenario +'_scenario.gif'), dpi=300, metadata={'artists':'Judith Verstegen & Sonja Holler'})

