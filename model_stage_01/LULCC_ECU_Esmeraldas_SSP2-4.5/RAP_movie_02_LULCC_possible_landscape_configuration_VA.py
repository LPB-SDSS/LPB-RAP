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
plt.switch_backend('agg')
import numpy as np
import matplotlib as mpl
colormap = mpl.colormaps['viridis'].resampled(18)
colormap_magma = mpl.colormaps['magma'].resampled(5)
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
RAP_population_and_LUTs_shares_dictionary = json.loads(sys.argv[1])

Population_value_list = RAP_population_and_LUTs_shares_dictionary['population']
Smallholder_value_list = RAP_population_and_LUTs_shares_dictionary['smallholder_share']
Agroforestry_value_list = RAP_population_and_LUTs_shares_dictionary['RAP_agroforestry']
Plantation_value_list = RAP_population_and_LUTs_shares_dictionary['RAP_plantation']
Reforestation_value_list = RAP_population_and_LUTs_shares_dictionary['RAP_reforestation']
Other_Ecosystems_value_list = RAP_population_and_LUTs_shares_dictionary['RAP_other_ecosystems']
Restoration_degraded_forest_value_list = RAP_population_and_LUTs_shares_dictionary['RAP_restoration_of_degraded_forest']

##############
### inputs ###
##############
if Parameters.get_mplc_with_maximum_anthropogenic_impact_simulation_decision() == True:
    anthropogenic_impact_simulation = '* simulation conducted WITH additional allocation for depiction of maximum anthropogenic impact'
else:
    anthropogenic_impact_simulation = '* simulation conducted WITHOUT additional allocation for depiction of maximum anthropogenic impact'

disclaimer_text = '** LAND USE BASED INDIVIDUAL ENTRY POINTS TO FLR - NOT A CHRONOLOGICAL SEQUENCE!'

## SH: LPB alternation
timesteps = Parameters.get_number_of_time_steps()
init_year = Parameters.get_initial_simulation_year()
country = Parameters.get_country()
region = Parameters.get_region()
baseline_scenario = Parameters.get_model_baseline_scenario()
model_scenario = Parameters.get_model_scenario()
fn = 'RAP'

## SH: LPB alternation
list_all_colors = {0:'white',
                   1:colormap(1),
                   4:colormap(4),
                   5:colormap(5),
                   6:colormap(6),
                   7:colormap(7),
                   8:colormap(8),
                   9:colormap(9),
                   10:colormap(10),
                   11:colormap(11),
                   12:colormap(12),
                   13:colormap(13),
                   18:colormap(18),
                   21:'greenyellow',
                   22:'springgreen',
                   23:'lime',
                   24:'aqua',
                   25:'lightgreen'}

list_all_names = {1:'01 = Built-up',
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
                   18:'18 = Plantation - - harvested',
                   21:'21 = RAP agroforestry',
                   22:'22 = RAP plantation',
                   23:'23 = RAP reforestation',
                   24:'24 = RAP other ecosystems',
                   25:'25 = RAP restoration of degraded forest'}

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
in_fn = os.path.join(Filepaths.folder_RAP_POSSIBLE_LANDSCAPE_CONFIGURATION,  fn + nr_zeros * '0' + '.001')
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

year = axarr.text(-0.2, 0.9, '', transform=axarr.transAxes, size=5)

population = axarr.text(-0.2, 0.86, '', transform=axarr.transAxes, size=5, color='firebrick')
smallholder = axarr.text(-0.2, 0.83, '', transform=axarr.transAxes, size=5, color='firebrick')

RAP_agroforestry = axarr.text(-0.2, 0.80, '', transform=axarr.transAxes, size=5)
RAP_plantations = axarr.text(-0.2, 0.77, '', transform=axarr.transAxes, size=5)
RAP_reforestation = axarr.text(-0.2, 0.74, '', transform=axarr.transAxes, size=5)
RAP_other_ecosystems = axarr.text(-0.2, 0.71, '', transform=axarr.transAxes, size=5)
RAP_restoration_of_degraded_forest = axarr.text(-0.2, 0.68, '', transform=axarr.transAxes, size=5)

anthropogenic_impact = axarr.text(-0.25, -0.07, '', size=6, transform=axarr.transAxes)
disclaimer = axarr.text(-0.25, -0.1, '', size=6, transform=axarr.transAxes)

## SH: LPB alternation
# JV: use imshow to plot the raster over time in two functions for the animation
def init():
    im = axarr.imshow(data, norm=norm_without_mv, zorder=0,\
                            cmap=cmap_long, animated=True, interpolation='nearest')
    return im, leg, year, subtitle, title_annotation, title

## SH: LPB alternation
def animate(i):
    position = i
    Population_value = Population_value_list[position]
    Smallholder_value = Smallholder_value_list[position]
    Agroforestry_value = Agroforestry_value_list[position]
    Plantation_value = Plantation_value_list[position]
    Reforestation_value = Reforestation_value_list[position]
    Other_Ecosystems_value = Other_Ecosystems_value_list[position]
    Restoration_degraded_forest_value = Restoration_degraded_forest_value_list[position]

    t = i + 1
    if t < 10:
        fn = in_fn[:-3] + '00' + str(t)
    else:
        fn = in_fn[:-3] + '0' + str(t)
    amap = readmap(fn)
    data = pcr2numpy(amap, 0)
    im = axarr.imshow(data, norm=norm_without_mv, zorder=0,\
                            cmap=cmap_long, animated=True, interpolation='nearest')

    disclaimer.set_text(disclaimer_text)
    anthropogenic_impact.set_text(anthropogenic_impact_simulation)

    RAP_restoration_of_degraded_forest.set_text('RAP restoration of degraded forest: ' + str(Restoration_degraded_forest_value) + str(' ') + str(Parameters.get_pixel_size()))
    RAP_other_ecosystems.set_text('RAP other ecosystems: ' + str(Other_Ecosystems_value) + str(' ') + str(Parameters.get_pixel_size()))
    RAP_reforestation.set_text('RAP reforestation: ' + str(Reforestation_value) + str(' ') + str(Parameters.get_pixel_size()))
    RAP_plantations.set_text('RAP plantation: ' + str(Plantation_value) + str(' ') + str(Parameters.get_pixel_size()))
    RAP_agroforestry.set_text('RAP agroforestry: '+ str(Agroforestry_value) + str(' ') + str(Parameters.get_pixel_size()))
    smallholder.set_text('Smallholder: ' + str(Smallholder_value) + str(' '))
    population.set_text('Population: ' + str(Population_value) + str(' '))
    year.set_text('Year = ' + str(init_year + t - 1))
    subtitle.set_text(country + ' ' + region + ' ' + baseline_scenario + ' ' + model_scenario + '-scenario')
    title_annotation.set_text(' - simulated FLR suggested Restoration Area Potentials (RAP) **')
    title.set_text('RAP LULCC SIMULATION - possible landscape configuration *')
    return im, leg, year, subtitle, title_annotation, title

im_ani = animation.FuncAnimation(f, animate, interval=300, \
                                   blit=False, frames = timesteps,\
                                   init_func=init)
im_ani.save(os.path.join(Filepaths.folder_RAP_GIFs, filename +'_' + country +'_' + region + '_' + model_scenario +'_scenario.gif'), dpi=300, metadata={'artists':'Judith Verstegen & Sonja Holler'})


