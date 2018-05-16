import ROOT


def get_plots(outfile):
    """Initialize plots and directories within the currently focused root file."""
    plots = {}

    plots['EventsByHits'] = ROOT.TH1D(
        'EventsByHits', 'Events by Hit Count', 100, 0, 100)
    plots['trkPt'] = ROOT.TH1D('trkPt', 'Track pT', 100, 0, 100)
    plots['trkNLcts'] = ROOT.TH1D('trkNLcts', 'Track # LCTs', 5, 0, 5)

    # Objects by Lumi Section
    outfile.mkdir("XbyLS").cd()
    for obj in ['Events', 'LCTs', 'Chambers', 'Tracks']:
        plots[obj + 'ByLS'] = ROOT.TH1D(obj + 'ByLS',
                                        obj + ' by LS', 1000, 0, 1000)
        plots[obj + 'ByLS'].GetXaxis().SetTitle('Lumi Section #')

    # Objects by PileUp
    outfile.mkdir("XbyPU").cd()
    for obj in ['Events', 'LCTs', 'Chambers', 'Tracks']:
        plots[obj + 'ByPU'] = ROOT.TH1D(obj +
                                        'ByPU', obj + ' by PU', 100, 0, 100)
        plots[obj + 'ByPU'].GetXaxis().SetTitle('Lumi Section Avg Pileup')

    # Objects by Delivered Luminosity
    outfile.mkdir("XbyDelLumi").cd()
    for obj in ['Events', 'LCTs', 'Chambers', 'Tracks']:
        plots[obj + 'ByDelLumi'] = ROOT.TH1D(obj + 'ByDelLumi',
                                             obj + ' by Delivered Lumi', 20000, 0, 20000)
        plots[obj + 'ByDelLumi'].GetXaxis().SetTitle('Lumi Section Delivered Lumi')

    return plots


def post_fill(outfile, plots):
    """Perform derivative operations on filled plots."""

    outfile.cd()

    # Make division plots: a/Event by b
    for a in ['LCTs', 'Chambers']:
        for b in ['LS', 'PU', 'DelLumi']:
            p = plots[a + 'By' + b].Clone(a + 'OEvtsBy' + b)
            p.SetTitle(a + '/Event by' + b)
            p.Divide(plots['EventsBy' + b])
            plots[a + 'OEvtsBy' + b] = p

    # Linear fit each plot
    ROOT.gStyle.SetOptFit(1)
    for p in plots:
        plots[p].Fit("pol1")
