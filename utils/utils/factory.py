import epics as e

def mk_pv(base, ext):
    return e.PV(base + ':' + ext)
