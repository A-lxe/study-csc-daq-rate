#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A collection of utilities extracted from the code to improve clarity and reusability."""


def locations():
    """All possible endcap, station, ring locations for a CSC chamber.

    Includes locations with '+-' or 'All' filling the ec, stat, and or ring.
    """
    return (location(ec, stat, ring)
            for ec in ['+-', '+', '-']
            for stat in ['All', '1', '2', '3', '4']
            for ring in ['All', '1', '1a', '1b', '2', '3']
            if not (stat not in ['All', '1'] and ring in ['1a', '1b', '3']))


def location(endcap, station, ring):
    return 'ME{}{}/{}'.format(endcap, station, ring)


def plot_id(obj, by=None, loc=None):
    pid = obj
    if by:
        pid += "_by_{}".format(by)
    if loc:
        pid += "_in_{}".format(loc)
    return pid.lower()


def plot_name(obj, by=None, loc=None):
    pid = obj
    if by:
        pid += " By {}".format(by)
    if loc:
        pid += " In {}".format(loc)
    return pid


def lct_cut(event, lct):
    """Return true if lct isn't CSC or is a neighbor."""
    return (
        not event.hit_isCSC[lct] or
        event.hit_neighbor[lct]
    )


def is_emtf_singlemu22_event(event):
    for trk in range(event.nTracks):
        if is_emtf_singlemu22_track(event, trk):
            return True
    return False


def is_emtf_singlemu22_track(event, track):
    pT = event.trk_pt[track]
    nHits = event.trk_nHits[track]
    quality = 0b0
    for hitIdx in range(nHits):
        hit = event.trk_iHit[track][hitIdx]
        quality |= 1 << (4 - event.hit_station[hit])
    assert quality < 16

    return (
        pT >= 22 and
        quality in {15, 14, 13, 11}
    )


def fill_plot(plots, obj, by, endcap, station, ring, value):
    if station == 1 and ring == 1:
        fill_plot(plots, obj, by, endcap, station, '1a', value)
        ring = 1
    elif station == 1 and ring == 4:
        fill_plot(plots, obj, by, endcap, station, '1b', value)
        ring = 1

    ring_vals = [ring] if station == 1 and ring == 1 else ['All', ring]
    # Iterate over all locations of filling All/+- instead of the actual value
    for loc in (location(ec, stat, r)
                for ec in ['+-', endcap]
                for stat in ['All', station]
                for r in ring_vals):
        pid = plot_id(obj, by, loc)
        plots[pid].Fill(value)
