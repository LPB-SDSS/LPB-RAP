"""LAFORET-PLUC-BE-RAP/SFM - FORMULAS
Sonja Holler (SH), Melvin Lippe (ML) and Daniel Kuebler (DK), 2021 Q2/Q3
This document provides a short method how to generate PCRaster conform output for the nested sub-folder structure."""

def generate_PCRaster_conform_output_for_subfolder(pcraster_conform_map_name, time_step):
    # test if the name has 8 characters, else append 0 until 8 characters
    length_of_characters = len(pcraster_conform_map_name)
    if length_of_characters < 8:
        while length_of_characters < 8:
            pcraster_conform_map_name = pcraster_conform_map_name + str(0)
            length_of_characters += 1
    else:
        pass
    output_map_name = pcraster_conform_map_name
    # append the time step in format .001 WITH SELF.REPORT IN LANDUSECHANGEMODEL THIS PART IS NOT NEEDED
    length_of_time_step = len(str(time_step))
    if length_of_time_step == 1:
        output_map_name = pcraster_conform_map_name + '.00' + str(time_step)
    elif length_of_time_step == 2:
        output_map_name = pcraster_conform_map_name + '.0' + str(time_step)
    elif length_of_time_step == 3:
        output_map_name = pcraster_conform_map_name + '.' + str(time_step)
    return output_map_name