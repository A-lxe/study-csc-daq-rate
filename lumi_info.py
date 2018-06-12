#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Throwaway code for parsing luminosity information from csv's produced by brilcalc.

https://cms-service-lumi.web.cern.ch/cms-service-lumi/brilwsdoc.html
"""
import csv


class LumiInfo(object):
    """Parses lumi_info csvs from brilcalc and provides their information by run+LS."""

    ls_info = {}

    def load_csv(self, fname):
        """Load a lumi_info csv into cache."""
        with open(fname, 'r') as f:
            reader = csv.reader(f)

            tag_header = next(reader)
            header = next(reader)
            header[0] = header[0][1:]  # Remove leading '#'

            for row in reader:
                if row[0][0] == '#':
                    break
                info = {h: val for (h, val) in zip(header, row)}
                run = int(info["run:fill"].split(':')[0])
                ls = int(info["ls"].split(':')[0])
                self.ls_info[(run, ls)] = info

    def get_info(self, run, ls):
        """Return the info from a row as a dict."""
        return self.ls_info[(int(run), int(ls))]

    def print_all(self):
        """Print every row of lumi info in this."""
        for ls in self.ls_info:
            print('{0}: {1}'.format(ls, self.ls_info[ls]))

