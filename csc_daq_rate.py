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
import ROOT
import os
import sys
from collections import defaultdict
from helpers import lct_cut, location, fill_plot, plot_id
from lumi_info import LumiInfo
from plots import get_plots, post_fill


# Constants -------------------------------------------------------------------

MAX_EVT = 2000000

DATA_DIR = "data/"
LUMI_INFO_DIR = "lumi_info/"

PLOTS_OUTPUT_ZB = "out/plots_zerobias.root"
FILES_ZB = [DATA_DIR + f for f in [
    "NTuple_ZeroBias1_FlatNtuple_Run_306091_2018_03_02_ZB1.root",
]]

PLOTS_OUTPUT_SM = "out/plots_singlemu.root"
FILES_SM = [DATA_DIR + f for f in [
    "NTuple_SingleMuon_FlatNtuple_Run_306092_2018_03_02_SingleMu.root",
    "NTuple_SingleMuon_FlatNtuple_Run_306135_2018_03_02_SingleMu.root",
    "NTuple_SingleMuon_FlatNtuple_Run_306154_2018_03_02_SingleMu.root",
]]

LUMI_FILES= [LUMI_INFO_DIR + f for f in [
    "LumiInfo_306091.csv",
    "LumiInfo_306092.csv",
    "LumiInfo_306135.csv",
    "LumiInfo_306154.csv",
]]


def run(input_files=FILES_ZB, output_file=PLOTS_OUTPUT_ZB):

    # Print run information ---------------------------------------------------

    print('Max events: {}'.format(MAX_EVT))
    print('Output file: {}'.format(output_file))
    print('Input files: ')
    for f in input_files:
        print('\t{}'.format(f))
    print('Lumi Info files: ')
    for f in LUMI_FILES:
        print('\t{}'.format(f))
    print('')

    # Set ROOT options --------------------------------------------------------

    ROOT.gROOT.SetBatch(ROOT.kTRUE)

    # Prepare input/output ----------------------------------------------------

    # Create output directory/file
    if not os.path.exists(os.path.dirname(output_file)):
        os.makedirs(os.path.dirname(output_file))
    output_file=ROOT.TFile(output_file, "RECREATE")

    # Load plots from ./plots.py
    p=get_plots(output_file)

    # Load ntuple files
    chain=ROOT.TChain("FlatNtupleData/tree")
    for f in input_files:
        chain.Add(f)

    # Load lumi info files
    lumi_info=LumiInfo()
    for f in LUMI_FILES:
        lumi_info.load_csv(f)

    # Event loop --------------------------------------------------------------

    # Technically event is the same TChain pointer as chain, but iterating
    # updates the event index. Enumerate just lets counter hold the number of
    # events processed
    for counter, event in enumerate(chain):
        if counter % 1000 == 0:
            print("Processed {} events".format(counter))
        if counter > MAX_EVT:
            break

        ls=event.evt_LS
        # NOTE these use hardcoded keys from the lumi info
        pu=float(lumi_info.get_info(
            event.evt_run, event.evt_LS)['avgpu'])
        del_lumi=float(lumi_info.get_info(
            event.evt_run, event.evt_LS)['delivered(1e30/cm2s)']) / 10000

        p['EventsByHits'].Fill(event.nHits)
        p['EventsByLS'].Fill(ls)
        p['EventsByPU'].Fill(pu)
        p['EventsByDelLumi'].Fill(del_lumi)

        # Keep track of chamber occupancies
        chambers=defaultdict(lambda: 0)

        for lct in range(event.nHits):
            if lct_cut(event, lct):
                continue
            endcap='+' if event.hit_endcap[lct] == 1 else '-'
            station=event.hit_station[lct]
            ring=event.hit_ring[lct]
            chamber=event.hit_chamber[lct]

            # Add an LCT to the chamber
            chambers[(
                endcap, station, ring, chamber
            )] += 1

        for c in chambers:
            fill_plot(p, 'Chambers', 'LS', c[0], c[1], c[2], ls)
            fill_plot(p, 'Chambers', 'PU', c[0], c[1], c[2], pu)
            fill_plot(p, 'Chambers', 'DelLumi', c[0], c[1], c[2], del_lumi)

            # Plot at most 2 LCTs per chamber
            count=min(2, chambers[c])
            for i in range(chambers[c]):
                fill_plot(p, 'LCTs', 'LS', c[0], c[1], c[2], ls)
                fill_plot(p, 'LCTs', 'PU', c[0], c[1], c[2], pu)
                fill_plot(p, 'LCTs', 'DelLumi', c[0], c[1], c[2], del_lumi)

        for trk in range(event.nTracks):
            p['trkPt'].Fill(event.trk_pt[trk])
            p['trkNLcts'].Fill(event.trk_nHits[trk])

            loc=location('+-', 'All', 'All')
            p[plot_id('Tracks', 'LS', loc)].Fill(ls)
            p[plot_id('Tracks', 'PU', loc)].Fill(ls)
            p[plot_id('Tracks', 'DelLumi', loc)].Fill(ls)

    # Cleanup -----------------------------------------------------------------

    post_fill(output_file, p)
    output_file.Write()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == 'singlemu':
        run(input_files=FILES_SM, output_file=PLOTS_OUTPUT_SM)
    else:
        run()
