#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Analysis code for studying the CSC L1T DAQ data rate via EMTF LCTs.

See
https://github.com/chadfreer/cmssw/tree/LCT-Matched-Plotter/EMTFAnalyzer/NTupleMaker
for a list of values available in the NTuples used.

Data sourced from 
/eos/cms/store/user/abrinke1/EMTF/Emulator/ntuples/HADD/

Lumi info sourced via brilcalc
https://cms-service-lumi.web.cern.ch/cms-service-lumi/brilwsdoc.html

Author: Alex Aubuchon
"""
import os
import ROOT
from lumi_info import LumiInfo
from plots import get_plots, post_fill
from helpers import lct_cut


# Constants -------------------------------------------------------------------

MAX_EVT = 10000
PLOTS_OUTPUT = "out/plots_zerobias.root"

DATA_DIR = "data/"
LUMI_INFO_DIR = "lumi_info/"

FILES = map(lambda f: DATA_DIR + f, [
    "NTuple_ZeroBias1_FlatNtuple_Run_306091_2018_03_02_ZB1.root",
    # "NTuple_SingleMuon_FlatNtuple_Run_306092_2018_03_02_SingleMu.root",
    # "NTuple_SingleMuon_FlatNtuple_Run_306135_2018_03_02_SingleMu.root",
    # "NTuple_SingleMuon_FlatNtuple_Run_306154_2018_03_02_SingleMu.root",
])

LUMI_FILES = map(lambda f: LUMI_INFO_DIR + f, [
    "LumiInfo_306091.csv",
    "LumiInfo_306092.csv",
    "LumiInfo_306135.csv",
    "LumiInfo_306154.csv",
])


def run():

    # Set ROOT options --------------------------------------------------------

    ROOT.gROOT.SetBatch(ROOT.kTRUE)

    # Prepare input/output ----------------------------------------------------

    # Create output directory/file
    if not os.path.exists(os.path.dirname(PLOTS_OUTPUT)):
        os.makedirs(os.path.dirname(PLOTS_OUTPUT))
    output_file = ROOT.TFile(PLOTS_OUTPUT, "RECREATE")

    # Load plots from ./plots.py
    p = get_plots(output_file)

    # Load ntuple files
    chain = ROOT.TChain("FlatNtupleData/tree")
    for f in FILES:
        chain.Add(f)

    # Load lumi info files
    lumi_info = LumiInfo()
    for f in LUMI_FILES:
        lumi_info.load_csv(f)

    # Event loop --------------------------------------------------------------

    # Technically event is the same TChain pointer as chain, but iterating
    # updates the event index. Enumerate just lets counter hold the number of
    # events processed
    for counter, event in enumerate(chain):
        if counter % 1000 == 0:
            print("Processed {0} events".format(counter))
        if counter > MAX_EVT:
            break

        # NOTE these use hardcoded keys from the lumi info
        pu = float(lumi_info.get_info(
            event.evt_run, event.evt_LS)['avgpu'])
        del_lumi = float(lumi_info.get_info(
            event.evt_run, event.evt_LS)['delivered(1e30/cm2s)'])

        p['EventsByHits'].Fill(event.nHits)
        p['EventsByLS'].Fill(event.evt_LS)
        p['EventsByPU'].Fill(pu)
        p['EventsByDelLumi'].Fill(del_lumi)

        # Keep track of unique chambers
        chambers = set()

        for lct in range(event.nHits):
            if lct_cut(event, lct):
                continue
            chambers.add((
                event.hit_endcap[lct],
                event.hit_station[lct],
                event.hit_ring[lct],
                event.hit_chamber[lct]
            ))
            p['LCTsByLS'].Fill(event.evt_LS)
            p['LCTsByPU'].Fill(pu)
            p['LCTsByDelLumi'].Fill(del_lumi)

        for chamber in chambers:
            p['ChambersByLS'].Fill(event.evt_LS)
            p['ChambersByPU'].Fill(pu)
            p['ChambersByDelLumi'].Fill(del_lumi)

        for trk in range(event.nTracks):
            p['trkPt'].Fill(event.trk_pt[trk])
            p['trkNLcts'].Fill(event.trk_nHits[trk])
            p['TracksByLS'].Fill(event.evt_LS)
            p['TracksByPU'].Fill(pu)
            p['TracksByDelLumi'].Fill(del_lumi)

    # Cleanup -----------------------------------------------------------------

    post_fill(output_file, p)
    output_file.Write()


if __name__ == "__main__":
    run()
