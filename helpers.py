#!/usr/bin/env python
# -*- coding: utf-8 -*-


def lct_cut(event, lct):
    """Return true if lct isn't CSC or is a neighbor"""
    return (
        event.hit_isCSC[lct] or
        event.hit_neighbor[lct]
    )
