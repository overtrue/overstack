"""Printer-specific settings within two build-plate size groups."""
TARGETS={
    'x2d':{'folder':'','group':'256','printer':'Bambu Lab X2D','area':[0,0,256,256],'height':260,'bed':[256,256]},
    'h2s':{'folder':'bed-h/h2s','group':'h-series','printer':'Bambu Lab H2S','area':[0,0,340,320],'height':340,'bed':[340,320]},
    # Use the intersection of both nozzle areas/heights, not their combined envelope.
    'h2c':{'folder':'bed-h/h2c','group':'h-series','printer':'Bambu Lab H2C','area':[25,0,325,320],'height':320,'bed':[330,320]},
}
