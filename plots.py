import ROOT
from helpers import locations, location, plot_id, plot_name


def get_plots(outfile):
    """Initialize plots and directories within the currently focused root file."""
    plots = {}

    # X Axis Parameters by the 'By' parameter
    x_axis_ranges = {
        'Hits': (100, 0, 100),
        'LS': (1000, 0, 1000),
        'PU': (100, 0, 100),
        'DelLumi': (250, 0, 2.5)
    }
    x_axis_titles = {
        'Hits': 'LCT Count',
        'LS': 'Lumi Section #',
        'PU': 'Lumi Section PileUp',
        'DelLumi': 'Lumi Section Delivered Luminosity [1e34cm^-2s^-1]'
    }

    # Event Plots
    for evt_type in ['Events', 'EMTF-SMuQual-Events']:
        for by in ['Hits', 'LS', 'PU', 'DelLumi']:
            root_id = plot_id(evt_type, by)
            name = plot_name(evt_type, by)
            xar = x_axis_ranges[by]

            plots[root_id] = ROOT.TH1D(root_id, name,
                                       xar[0], xar[1], xar[2])
            plots[root_id].GetXaxis().SetTitle(x_axis_titles[by])

    # Track Summary Info
    plots['trkPt'] = ROOT.TH1D('trkPt', 'Track pT', 100, 0, 100)
    plots['trkNLcts'] = ROOT.TH1D('trkNLcts', 'Track # LCTs', 5, 0, 5)

    # Loop over observed objects, over x axis, and over location
    # (ie LCTs by PU in ME+1/2)
    for obj in ['LCTs', 'Chambers', 'Tracks']:
        dirA = outfile.mkdir(obj)
        for by in ['LS', 'PU', 'DelLumi']:
            dirA.mkdir('by{}'.format(by)).cd()
            for loc in locations():
                name = plot_name(obj, by, loc)
                root_id = plot_id(obj, by, loc)
                xar = x_axis_ranges[by]

                plots[root_id] = ROOT.TH1D(root_id, name,
                                           xar[0], xar[1], xar[2])
                plots[root_id].GetXaxis().SetTitle(x_axis_titles[by])

    # Enable tracking sum of squares of weights
    for p in plots:
        plots[p].Sumw2()

    return plots


def post_fill(outfile, plots):
    """Perform derivative operations on filled plots."""

    outfile.cd()

    # Loop over observed objects, over x axis, and over location
    # (ie LCTs by PU in ME+1/2)
    for obj in ['LCTs', 'Chambers', 'Tracks']:
        dirA = outfile.mkdir(obj + 'PerEvent')
        for by in ['LS', 'PU', 'DelLumi']:
            dirA.mkdir('by{}'.format(by)).cd()
            for loc in locations():
                obj_plotid = plot_id(obj, by, loc)
                events_plotid = plot_id('Events', by)

                new_obj = "{}-Per-Event".format(obj)
                name = plot_name(new_obj, by, loc)
                root_id = plot_id(new_obj,  by, loc)

                # Divide the plot by the corresponding Events plot
                p = plots[obj_plotid].Clone(root_id)
                p.SetTitle(name)
                p.Divide(plots[events_plotid])
                plots[root_id] = p

            # Copy the ME+-All/All plot to the parent directory
            dirA.cd()
            new_obj = "{}-Per-Event".format(obj)
            summary_id = plot_id(new_obj, by, location('+-', 'All', 'All'))
            p = plots[summary_id].Clone(plot_id(new_obj, by))
            plots[plot_id(new_obj, by)] = p

    # Linear fit each plot
    ROOT.gStyle.SetOptFit(1)
    for p in plots:
        plots[p].Fit('pol1', 'W')
