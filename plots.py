import ROOT
from helpers import locations, location, plot_id, plot_name


def get_plots(outfile):
    """Initialize plots and directories within the currently focused root file."""
    plots = {}

    # Event Plots
    plots['EventsByHits'] = ROOT.TH1D(
        'EventsByHits', 'Events by Hit Count', 100, 0, 100)
    plots['EventsByLS'] = ROOT.TH1D(
        'EventsByLS', 'Events by LS', 1000, 0, 1000)
    plots['EventsByPU'] = ROOT.TH1D(
        'EventsByPU', 'Events by PU', 100, 0, 100)
    plots['EventsByDelLumi'] = ROOT.TH1D(
        'EventsByDelLumi', 'Events by DelLumi', 2500, 0, 2.5)

    # Track Summary Info
    plots['trkPt'] = ROOT.TH1D('trkPt', 'Track pT', 100, 0, 100)
    plots['trkNLcts'] = ROOT.TH1D('trkNLcts', 'Track # LCTs', 5, 0, 5)

    # X Axis Parameters by the 'By' parameter
    x_axis_ranges = {
        'LS': (1000, 0, 1000),
        'PU': (100, 0, 100),
        'DelLumi': (2500, 0, 2.5)
    }
    x_axis_titles = {
        'LS': 'Lumi Section #',
        'PU': 'Lumi Section PileUp',
        'DelLumi': 'Lumi Section Delivered Luminosity'
    }

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
                events_plotid = 'EventsBy' + by

                name = "{} Per Event By {} In {}".format(obj, by, loc)
                root_id = name.replace(' ', '')

                # Divide the plot by the corresponding Events plot
                p = plots[obj_plotid].Clone(root_id)
                p.SetTitle(name)
                p.Divide(plots[events_plotid])
                plots[root_id] = p

            # Copy the ME+-All/All plot to the parent directory
            dirA.cd()
            summary_id = "{}PerEventBy{}In{}".format(
                obj, by, location('+-', 'All', 'All'))
            p = plots[summary_id].Clone('{}PerEventBy{}'.format(obj, by))
            plots['{}PerEventBy{}'.format(obj, by)] = p

    # Linear fit each plot
    ROOT.gStyle.SetOptFit(1)
    for p in plots:
        plots[p].Fit('pol1', 'W')  # Linear fit with all non-empty weights = 1
