"""LAFORET-PLUC-BE-RAP/SFM - LPB_movie_land_use 
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
import sys, ast
import json

# # get the dictionary
number_of_samples_set = json.loads(sys.argv[1])

# to get a visualisation of the maximum distance impact around settlements get the last sample number
# print('TEST type', type(ast.literal_eval(sys.argv[1])))
# print('TEST value', ast.literal_eval(sys.argv[1]))
# number_of_samples_set = int(ast.literal_eval(sys.argv[1]))
print('number_of_samples_set:', number_of_samples_set)

plt.switch_backend('agg')
import numpy as np
import os
from pcraster import *
import Parameters
import Filepaths

##############
### inputs ###
##############

## SH: LPB alternation
timesteps = Parameters.get_number_of_time_steps()
init_year = Parameters.get_initial_simulation_year()
country = Parameters.get_country()
region = Parameters.get_region()
baseline_scenario = Parameters.get_model_baseline_scenario()
model_scenario = Parameters.get_model_scenario()
fn = 'LPBLULCC'

## SH: LPB alternation
list_all_colors = {0:'white',
                   1:'crimson',
                   2:'gold',
                   3:'palegreen',
                   4:'olivedrab',
                   5:'teal',
                   6:'moccasin',
                   7:'chocolate',
                   8:'limegreen',
                   9:'darkgreen',
                   10:'powderblue',
                   11:'lavender',
                   12:'steelblue',
                   13:'slategrey',
                   14:'orange',
                   15:'lime',
                   16:'blueviolet',
                   17:'deeppink',
                   18:'fuchsia'}

list_all_names = {1:'01 = Built-up',
                   2:'02 = Cropland-annual',
                   3:'03 = Pasture',
                   4:'04 = Agroforestry',
                   5:'05 = Plantation',
                   6:'06 = Herbaceous vegetation',
                   7:'07 = Shrubs',
                   8:'08 = Disturbed Forest',
                   9:'09 = Undisturbed Forest',
                   10:'10 = Moss, lichen, bare, sparse vegetation',
                   11:'11 = Herbaceous wetland',
                   12:'12 = Water',
                   13:'13 = No input',
                   14:'14 = Cropland-annual - - abandoned',
                   15:'15 = Pasture - - abandoned',
                   16:'16 = Agroforestry - - abandoned',
                   17:'17 = Net Forest - - deforested',
                   18:'18 = Plantation - - harvested'}

## SH: LPB alternation
legend_loc = (0.975,0.175)  # Esmeraldas right bottom

############
### MAIN ###
############

########################################################################################################################
# 1st sample

## SH: LPB alternation
# SH: look up the files in the according new output folder
wd = os.getcwd()
# open the raster and read out the data in a numpy array
if (8 - len(fn)) > 0: nr_zeros = 8 - len(fn)
else:  nr_zeros = 0
in_fn = os.path.join(wd, Filepaths.folder_outputs, 'LPB', 'LULCC_simulation', 'dynamic_environment_map_probabilistic', '1',  fn + nr_zeros * '0' + '.001')
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

## SH: LPB alternation
# JV: use imshow to plot the raster over time in two functions for the animation
def init():
    im = axarr.imshow(data, norm=norm_without_mv, zorder=0,\
                            cmap=cmap_long, animated=True, interpolation='nearest')
    return im, leg, year, subtitle, title_annotation

## SH: LPB alternation
def animate(i):
    t = i + 1
    if t < 10:
        fn = in_fn[:-3] + '00' + str(t)
    else:
        fn = in_fn[:-3] + '0' + str(t)
    ##print fn
    amap = readmap(fn)
    data = pcr2numpy(amap, 0)
    im = axarr.imshow(data, norm=norm_without_mv, zorder=0,\
                            cmap=cmap_long, animated=True, interpolation='nearest')
    year.set_text('Year = ' + str(init_year + t - 1))
    subtitle.set_text(country + ' ' + region + ' ' + baseline_scenario + ' ' + model_scenario + '-scenario')
    title_annotation.set_text('1st probabilistic sample of ' + str(number_of_samples_set))
    title.set_text('LPB LULCC SIMULATION - basic probabilistic modelling')
    return im, leg, year, subtitle, title

im_ani = animation.FuncAnimation(f, animate, interval=300, \
                                   blit=False, frames = timesteps,\
                                   init_func=init)
im_ani.save(os.path.join(Filepaths.folder_GIFs, 'LPB_movie_01_LULCC_sample_1_' + country +'_' + region + '_' + baseline_scenario + '_' + model_scenario +'_scenario.gif'), dpi=300, metadata={'artists':'Judith Verstegen & Sonja Holler'})


########################################################################################################################
# Last sample

## SH: LPB alternation
# SH: look up the files in the according new output folder
wd = os.getcwd()
# open the raster and read out the data in a numpy array
if (8 - len(fn)) > 0: nr_zeros = 8 - len(fn)
else:  nr_zeros = 0
in_fn = os.path.join(wd, Filepaths.folder_outputs, 'LPB', 'LULCC_simulation', 'dynamic_environment_map_probabilistic', str(number_of_samples_set),  fn + nr_zeros * '0' + '.001')
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

## SH: LPB alternation
# JV: use imshow to plot the raster over time in two functions for the animation
def init():
    im = axarr.imshow(data, norm=norm_without_mv, zorder=0,\
                            cmap=cmap_long, animated=True, interpolation='nearest')
    return im, leg, year, subtitle, title_annotation

## SH: LPB alternation
def animate(i):
    t = i + 1
    if t < 10:
        fn = in_fn[:-3] + '00' + str(t)
    else:
        fn = in_fn[:-3] + '0' + str(t)
    ##print fn
    amap = readmap(fn)
    data = pcr2numpy(amap, 0)
    im = axarr.imshow(data, norm=norm_without_mv, zorder=0,\
                            cmap=cmap_long, animated=True, interpolation='nearest')
    year.set_text('Year = ' + str(init_year + t - 1))
    subtitle.set_text(country + ' ' + region + ' ' + baseline_scenario + ' ' + model_scenario + '-scenario')
    title_annotation.set_text('Last probabilistic sample of ' + str(number_of_samples_set))
    title.set_text('LPB LULCC SIMULATION - basic probabilistic modelling')
    return im, leg, year, subtitle, title

im_ani = animation.FuncAnimation(f, animate, interval=300, \
                                   blit=False, frames = timesteps,\
                                   init_func=init)
im_ani.save(os.path.join(Filepaths.folder_GIFs, 'LPB_movie_02_LULCC_sample_' + str(number_of_samples_set) + '_' + country +'_' + region + '_' + baseline_scenario + '_' + model_scenario +'_scenario.gif'), dpi=300, metadata={'artists':'Judith Verstegen & Sonja Holler'})


