import pathlib
import numpy as np
import pandas as pd
import pcraster as pcr
import Parameters



class TssGenerator(object):
    def __init__(self, classes, csvname):
        mv = -999
        
        year = int(Parameters.get_initial_simulation_year())

        self.dataframe = pd.read_csv(csvname)
        self.start_idx = self.dataframe.loc[self.dataframe["YEAR"] == year].index[0]

        new_df = pd.DataFrame()

        for col in classes:
            try:
                new_df[col] = self.dataframe.loc[self.start_idx:, str(col)]
            except KeyError:
                print(f"no column {col} in input file {csvname}")

        self.tss_dataframe = new_df.reset_index(drop=True)
        self.tss_dataframe.index += 1

        self.tss_filename = f"generated_tss_{pathlib.Path(csvname).stem}.tss"
        self._generate_tss()


    def value(self, timestep, column):
        idx = self.start_idx + timestep - 1
        return self.dataframe.loc[idx, str(column)]


    def tss_name(self):
        return self.tss_filename


    def _generate_tss(self):

        filename = self.tss_name()

        with open(filename, "w") as content:
            content.write("Generated file, do not edit\n")
            content.write(f"{self.tss_dataframe.shape[1] + 1}\n")
            content.write("model time steps\n")
            for col in self.tss_dataframe.columns:
                content.write(f"{col}\n")

        with open(filename, "a") as content:
            self.tss_dataframe.to_csv(content, header=False, sep=" ")
