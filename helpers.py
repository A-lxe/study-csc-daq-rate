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


def plot_id(obj, by, loc):
    return "{}By{}In{}".format(obj, by, loc)


def plot_name(obj, by, loc):
    return "{} By {} In {}".format(obj, by, loc)


def lct_cut(event, lct):
    """Return true if lct isn't CSC or is a neighbor."""
    return (
        not event.hit_isCSC[lct] or
        event.hit_neighbor[lct]
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
