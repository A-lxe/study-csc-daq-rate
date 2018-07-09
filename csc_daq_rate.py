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
import argparse
import ROOT
import os
from collections import defaultdict
from helpers import lct_cut, location, fill_plot, plot_id, is_emtf_singlemu22_event
from lumi_info import LumiInfo
from plots import get_plots, post_fill


# Constants -------------------------------------------------------------------

DATA_DIR = "data/"
LUMI_INFO_DIR = "lumi_info/"

FILES = {
    "zerobias_306091": [DATA_DIR + "NTuple_ZeroBias1_FlatNtuple_Run_306091_2018_03_02_ZB1.root"],
    "singlemu_306092": [DATA_DIR + "NTuple_SingleMuon_FlatNtuple_Run_306092_2018_03_02_SingleMu.root"],
    "singlemu_306135": [DATA_DIR + "NTuple_SingleMuon_FlatNtuple_Run_306135_2018_03_02_SingleMu.root"],
    "singlemu_306154": [DATA_DIR + "NTuple_SingleMuon_FlatNtuple_Run_306154_2018_03_02_SingleMu.root"],
    "zmu_306091": [DATA_DIR + "EMTF_ZMu_NTuple_306091_simLCT_test.root"],
    "zmu_316995": [DATA_DIR + "EMTF_ZMu_NTuple_316995_simLCT_test.root"],
    "zmu_317661": [DATA_DIR + "EMTF_ZMu_NTuple_317661_simLCT_test.root"],
}

LUMI_FILES = [LUMI_INFO_DIR +
              f for f in os.listdir(LUMI_INFO_DIR) if f[-4:] == '.csv']


# Main Function ---------------------------------------------------------------

def main():
    queries = [key for key in FILES]
    parser = argparse.ArgumentParser(description='Run AutoDQM offline.')
    parser.add_argument('query', type=str,
                        help="dataset to process. One of {}".format(queries))
    parser.add_argument('-n', '--event-count', type=int, default=1000000,
                        help="number of events to process")
    parser.add_argument('-o', '--output', type=str,
                        help="output filename")
    args = parser.parse_args()

    input_files = FILES[args.query]
    if not args.output:
        args.output = 'out/results-{}_{}-events.root'.format(
            args.query, args.event_count)
    run(input_files, args.output, args.event_count)


# Analysis Functions-----------------------------------------------------------

def run(input_files, output_file, max_events, verbose=True):

    # Print run information ---------------------------------------------------

    if verbose:
        print('Max events: {}'.format(max_events))
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
    output_file = ROOT.TFile(output_file, "RECREATE")

    # Load plots from ./plots.py
    p = get_plots(output_file)

    # Load ntuple files
    chain = ROOT.TChain("FlatNtupleData/tree")
    for f in input_files:
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
        if counter % 1000 == 0 and verbose:
            print("Processed {} events".format(counter))
        if counter >= max_events:
            break

        contains_emtf_smu = is_emtf_singlemu22_event(event)

        ls = event.evt_LS
        # NOTE these use hardcoded keys from the lumi info
        pu = float(lumi_info.get_info(
            event.evt_run, event.evt_LS)['avgpu'])
        del_lumi = float(lumi_info.get_info(
            event.evt_run, event.evt_LS)['delivered(1e30/cm2s)']) / 10000

        p['all-event_by_hits'].Fill(event.nHits)
        p['all-event_by_ls'].Fill(ls)
        p['all-event_by_pu'].Fill(pu)
        p['all-event_by_dellumi'].Fill(del_lumi)

        if contains_emtf_smu:
            p['emtf-smuqual-event_by_hits'].Fill(event.nHits)
            p['emtf-smuqual-event_by_ls'].Fill(ls)
            p['emtf-smuqual-event_by_pu'].Fill(pu)
            p['emtf-smuqual-event_by_dellumi'].Fill(del_lumi)
        else:
            p['not-emtf-smuqual-event_by_hits'].Fill(event.nHits)
            p['not-emtf-smuqual-event_by_ls'].Fill(ls)
            p['not-emtf-smuqual-event_by_pu'].Fill(pu)
            p['not-emtf-smuqual-event_by_dellumi'].Fill(del_lumi)

        # Keep track of chamber occupancies
        chambers = defaultdict(lambda: 0)
        bx0_chambers = defaultdict(lambda: 0)

        for lct in range(event.nHits):
            if lct_cut(event, lct):
                continue
            endcap = '+' if event.hit_endcap[lct] == 1 else '-'
            station = event.hit_station[lct]
            ring = event.hit_ring[lct]
            chamber = event.hit_chamber[lct]
            bx = event.hit_BX[lct]

            # Add an LCT to the chamber
            chambers[(
                endcap, station, ring, chamber
            )] += 1
            if bx == 0:
                bx0_chambers[(
                    endcap, station, ring, chamber
                )] += 1

        for c in chambers:
            fill_plot(p, 'All-Event-Chambers', 'LS', c[0], c[1], c[2], ls)
            fill_plot(p, 'All-Event-Chambers', 'PU', c[0], c[1], c[2], pu)
            fill_plot(p, 'All-Event-Chambers', 'DelLumi', c[0], c[1], c[2], del_lumi)
            if contains_emtf_smu:
                fill_plot(p, 'EMTF-SMuQual-Event-Chambers',
                          'LS', c[0], c[1], c[2], ls)
                fill_plot(p, 'EMTF-SMuQual-Event-Chambers',
                          'PU', c[0], c[1], c[2], pu)
                fill_plot(p, 'EMTF-SMuQual-Event-Chambers',
                          'DelLumi', c[0], c[1], c[2], del_lumi)
            else:
                fill_plot(p, 'Not-EMTF-SMuQual-Event-Chambers',
                          'LS', c[0], c[1], c[2], ls)
                fill_plot(p, 'Not-EMTF-SMuQual-Event-Chambers',
                          'PU', c[0], c[1], c[2], pu)
                fill_plot(p, 'Not-EMTF-SMuQual-Event-Chambers',
                          'DelLumi', c[0], c[1], c[2], del_lumi)

            # Plot at most 2 LCTs per chamber
            count = min(2, chambers[c])
            for i in range(count):
                fill_plot(p, 'All-Event-LCTs', 'LS', c[0], c[1], c[2], ls)
                fill_plot(p, 'All-Event-LCTs', 'PU', c[0], c[1], c[2], pu)
                fill_plot(p, 'All-Event-LCTs', 'DelLumi', c[0], c[1], c[2], del_lumi)
                if contains_emtf_smu:
                    fill_plot(p, 'EMTF-SMuQual-Event-LCTs',
                              'LS', c[0], c[1], c[2], ls)
                    fill_plot(p, 'EMTF-SMuQual-Event-LCTs',
                              'PU', c[0], c[1], c[2], pu)
                    fill_plot(p, 'EMTF-SMuQual-Event-LCTs',
                              'DelLumi', c[0], c[1], c[2], del_lumi)
                else:
                    fill_plot(p, 'Not-EMTF-SMuQual-Event-LCTs',
                              'LS', c[0], c[1], c[2], ls)
                    fill_plot(p, 'Not-EMTF-SMuQual-Event-LCTs',
                              'PU', c[0], c[1], c[2], pu)
                    fill_plot(p, 'Not-EMTF-SMuQual-Event-LCTs',
                              'DelLumi', c[0], c[1], c[2], del_lumi)
j
        for c in bx0_chambers:
            fill_plot(p, 'All-Event-BX0-Chambers', 'LS', c[0], c[1], c[2], ls)
            fill_plot(p, 'All-Event-BX0-Chambers', 'PU', c[0], c[1], c[2], pu)
            fill_plot(p, 'All-Event-BX0-Chambers', 'DelLumi', c[0], c[1], c[2], del_lumi)
            if contains_emtf_smu:
                fill_plot(p, 'EMTF-SMuQual-Event-BX0-Chambers',
                          'LS', c[0], c[1], c[2], ls)
                fill_plot(p, 'EMTF-SMuQual-Event-BX0-Chambers',
                          'PU', c[0], c[1], c[2], pu)
                fill_plot(p, 'EMTF-SMuQual-Event-BX0-Chambers',
                          'DelLumi', c[0], c[1], c[2], del_lumi)
            else:
                fill_plot(p, 'Not-EMTF-SMuQual-Event-BX0-Chambers',
                          'LS', c[0], c[1], c[2], ls)
                fill_plot(p, 'Not-EMTF-SMuQual-Event-BX0-Chambers',
                          'PU', c[0], c[1], c[2], pu)
                fill_plot(p, 'Not-EMTF-SMuQual-Event-BX0-Chambers',
                          'DelLumi', c[0], c[1], c[2], del_lumi)

            # Plot at most 2 LCTs per chamber
            count = min(2, chambers[c])
            for i in range(count):
                fill_plot(p, 'All-Event-BX0-LCTs', 'LS', c[0], c[1], c[2], ls)
                fill_plot(p, 'All-Event-BX0-LCTs', 'PU', c[0], c[1], c[2], pu)
                fill_plot(p, 'All-Event-BX0-LCTs', 'DelLumi', c[0], c[1], c[2], del_lumi)
                if contains_emtf_smu:
                    fill_plot(p, 'EMTF-SMuQual-Event-BX0-LCTs',
                              'LS', c[0], c[1], c[2], ls)
                    fill_plot(p, 'EMTF-SMuQual-Event-BX0-LCTs',
                              'PU', c[0], c[1], c[2], pu)
                    fill_plot(p, 'EMTF-SMuQual-Event-BX0-LCTs',
                              'DelLumi', c[0], c[1], c[2], del_lumi)
                else:
                    fill_plot(p, 'Not-EMTF-SMuQual-Event-BX0-LCTs',
                              'LS', c[0], c[1], c[2], ls)
                    fill_plot(p, 'Not-EMTF-SMuQual-Event-BX0-LCTs',
                              'PU', c[0], c[1], c[2], pu)
                    fill_plot(p, 'Not-EMTF-SMuQual-Event-BX0-LCTs',
                              'DelLumi', c[0], c[1], c[2], del_lumi)

        for trk in range(event.nTracks):
            p['all-event_trk-pt'].Fill(event.trk_pt[trk])
            p['all-event_trk-nlcts'].Fill(event.trk_nHits[trk])
            if contains_emtf_smu:
                p['emtf-smuqual-event_trk-pt'].Fill(event.trk_pt[trk])
                p['emtf-smuqual-event_trk-nlcts'].Fill(event.trk_nHits[trk])
            else:
                p['not-emtf-smuqual-event_trk-pt'].Fill(event.trk_pt[trk])
                p['not-emtf-smuqual-event_trk-nlcts'].Fill(
                    event.trk_nHits[trk])

            loc = location('+-', 'All', 'All')
            p[plot_id('All-Event-Tracks', 'LS', loc)].Fill(ls)
            p[plot_id('All-Event-Tracks', 'PU', loc)].Fill(ls)
            p[plot_id('All-Event-Tracks', 'DelLumi', loc)].Fill(ls)
            if contains_emtf_smu:
                p[plot_id('EMTF-SMuQual-Event-Tracks', 'LS', loc)].Fill(ls)
                p[plot_id('EMTF-SMuQual-Event-Tracks', 'PU', loc)].Fill(ls)
                p[plot_id('EMTF-SMuQual-Event-Tracks',
                          'DelLumi', loc)].Fill(ls)
            else:
                p[plot_id('Not-EMTF-SMuQual-Event-Tracks', 'LS', loc)].Fill(ls)
                p[plot_id('Not-EMTF-SMuQual-Event-Tracks', 'PU', loc)].Fill(ls)
                p[plot_id('Not-EMTF-SMuQual-Event-Tracks',
                          'DelLumi', loc)].Fill(ls)

    # Cleanup -----------------------------------------------------------------

    post_fill(output_file, p)
    output_file.Write()

    return p


if __name__ == "__main__":
    main()
