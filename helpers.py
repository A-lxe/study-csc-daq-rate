#!/usr/bin/env python
# -*- coding: utf-8 -*-


def lct_cut(event, lct):
    """Return true if lct passes the cut"""
    return (
        not event.hit_isCSC[lct] and
        not event.hit_neighbor[lct]
    )
