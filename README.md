# LPB-RAP

This is the repository for the scenario tool LPB-RAP (LaForeT-PLUC-BE-RAP model (Landscape Forestry in the Tropics – PCRaster Land Use Change – Biogeographic & Economic model; in short: LPB) and its thematic expansion module RAP (Restoration Areas Potentials)), including three available policy scenarios and optional potential habitat analysis. 

OPEN-ACCESS PUBLICATIONS:
Model stage 01, authored by Holler et al., 2024a, was published on February 2nd, 2024, in [PLOS ONE](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0297439).
Model stage 01 features 18 base LUTs + 5 RAP LUTs, the policy scenarios weak_conservation, enforced_conservation and no_conservation, as well as dichotomous modeling of a conventional land use landscape configuration development without Forest and Landscape Restoration (FLR) measures in contrast to a potential landscape-wide FLR introduction for each simulated time step.

Model stage 02, authored by Holler et al., 2024b, was published on December 30th, 2024, in [ECOLOGICAL MODELLING](https://doi.org/10.1016/j.ecolmodel.2024.111005)
Model stage 02 features 19 base LUTs + 5 RAP LUTs, the policy scenario weak_conservation, dynamic street network simulation and potential habitat analysis using user-defined ecosystem fragmentation, landscape metric(s) in PyLandStats and derivation of ecological landscape connectivity with integration of the Circuit-Theory approaches realized in Circuitscape and Omniscape.

This concludes the conceptual aspect of biogeographical analysis for flora and fauna within scenario LULCC.

BASE MODEL:
LPB-RAP is based on the [PCRaster Land Use Change model (PLUC) for Mozambique](https://github.com/JudithVerstegen/PLUC_Mozambique), created in [PCRaster](http://pcraster.geo.uu.nl/) Python. Results of the PLUC model are published in [Verstegen et al. 2012](https://doi.org/10.1016%2Fj.compenvurbsys.2011.08.003) and [van der Hilst et al. 2012](https://doi.org/10.1111/j.1757-1707.2011.01147.x).

MANUAL:
For more information, please first read the [LPB-RAP SDSS MANUAL](https://docs.google.com/document/d/1vBGS85Zng6-7PxjfsRx1r1kLTQsnpZikvcdYsh2Za34/edit?usp=sharing). The manual is updated with received questions and new materials.

CONTACT:
You can contact us under LPB.SDSS at gmail.com.

---------------

## Information

This repository contains all model files and input data for the case study area Esmeraldas province, Ecuador, for the exemplary SSP2-4.5 narrative simulated 2018–2100 in annual and hectare resolution. Due to data limitation only descriptive outputs are provided following the model output structure (R-outputs, GIFs, CSVs). The original PCRaster .map format output is too large to be provided in this repository (TB volume).
Model stage 01 contains the no FLR and potential FLR output for the three policy scenarios.
Model stage 02 contains the no FLR and potential FLR weak_conservation scenario for the umbrella species Jaguar, Panthera onca, including the postprocessing for derivation of the quantitative impact of potential FLR. The probing dates for the extended habitat analysis are 2024 and 2070.

