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
colormap = mpl.colormaps['viridis'].resampled(7)



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
RAP_potential_minimum_restoration_dictionary = json.loads(sys.argv[1])

Population_peak_value = RAP_potential_minimum_restoration_dictionary['population_peak_year']
Peak_demands_year_value = RAP_potential_minimum_restoration_dictionary['peak_demands_year']
LUT22_list = RAP_potential_minimum_restoration_dictionary['LUT22']
LUT23_list = RAP_potential_minimum_restoration_dictionary['LUT23']
LUT24_list = RAP_potential_minimum_restoration_dictionary['LUT24']
LUT25_list = RAP_potential_minimum_restoration_dictionary['LUT25']




##############
### inputs ###
##############
if Parameters.get_mplc_with_maximum_anthropogenic_impact_simulation_decision() == True:
    anthropogenic_impact_simulation = '* simulation conducted WITH additional allocation for depiction of maximum anthropogenic impact'
else:
    anthropogenic_impact_simulation = '* simulation conducted WITHOUT additional allocation for depiction of maximum anthropogenic impact'

disclaimer_text = '** population peak land use mask until population peak year'

## SH: LPB alternation
timesteps = Parameters.get_number_of_time_steps()
init_year = Parameters.get_initial_simulation_year()
country = Parameters.get_country()
region = Parameters.get_region()
baseline_scenario = Parameters.get_model_baseline_scenario()
model_scenario = Parameters.get_model_scenario()
fn = 'RAP_pmr'

## SH: LPB alternation
list_all_colors = {0:'white',
                   1:'black',
                   2:colormap(2),
                   3:colormap(3),
                   4:colormap(5),
                   5:colormap(7)
                   }

list_all_names = {1:'= region',
                   2:'= RAP plantation',
                   3:'= RAP reforestation',
                   4:'= RAP other ecosystems',
                   5:'= RAP restoration of degraded forest'
                   }

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
in_fn = os.path.join(Filepaths.folder_RAP_potential_minimum_restoration,  fn + nr_zeros * '0' + '.001')
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

year = axarr.text(-0.2, 0.90, '', transform=axarr.transAxes, size=5)

population_peak = axarr.text(-0.2, 0.86, '', transform=axarr.transAxes, size=5)
peak_demand_year = axarr.text(-0.2, 0.83, '', transform=axarr.transAxes, size=5)

LUT22 = axarr.text(-0.2, 0.80, '', transform=axarr.transAxes, size=5)
LUT23 = axarr.text(-0.2, 0.77, '', transform=axarr.transAxes, size=5)
LUT24 = axarr.text(-0.2, 0.74, '', transform=axarr.transAxes, size=5)
LUT25 = axarr.text(-0.2, 0.71, '', transform=axarr.transAxes, size=5)

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
    Plantation_value = LUT22_list[position]
    Reforestation_value = LUT23_list[position]
    Other_Ecosystems_value = LUT24_list[position]
    Restoration_of_degraded_forest_value =LUT25_list[position]
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

    LUT25.set_text('RAP restoration of degraded forest: ' + str(Restoration_of_degraded_forest_value) + str(' ') + str(Parameters.get_pixel_size()))
    LUT24.set_text('RAP other ecosystems: ' + str(Other_Ecosystems_value) + str(' ') + str(Parameters.get_pixel_size()))
    LUT23.set_text('RAP reforestation: ' + str(Reforestation_value) + str(' ') + str(Parameters.get_pixel_size()))
    LUT22.set_text('RAP plantation: ' + str(Plantation_value) + str(' ') + str(Parameters.get_pixel_size()))
    peak_demand_year.set_text('Peak demands year (user-defined scenario): ' + str(Peak_demands_year_value))
    population_peak.set_text('Population peak year (baseline scenario): ' + str(Population_peak_value))

    year.set_text('Year = ' + str(init_year + t - 1))
    subtitle.set_text(country + ' ' + region + ' ' + baseline_scenario + ' ' + model_scenario + '-scenario')
    title_annotation.set_text(' - potential minimum restoration area **')
    title.set_text('RAP LULCC SIMULATION - possible landscape configuration *')
    return im, leg, year, subtitle, title_annotation, title

im_ani = animation.FuncAnimation(f, animate, interval=300, \
                                   blit=False, frames = timesteps,\
                                   init_func=init)
im_ani.save(os.path.join(Filepaths.folder_RAP_GIFs, filename +'_' + country +'_' + region + '_' + model_scenario +'_scenario.gif'), dpi=300, metadata={'artists':'Judith Verstegen & Sonja Holler'})


