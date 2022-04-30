# greaseweazle/tools/util.py
#
# Greaseweazle control script: Utility functions.
#
# Written & released by Keir Fraser <keir.xen@gmail.com>
#
# This is free and unencumbered software released into the public domain.
# See the file COPYING for more details, or visit <http://unlicense.org>.

import argparse, os, sys, struct, time, re, platform
import importlib
from collections import OrderedDict

from .. import error


class CmdlineHelpFormatter(argparse.ArgumentDefaultsHelpFormatter,
                           argparse.RawDescriptionHelpFormatter):
    def _get_help_string(self, action):
        help = action.help
        if '%no_default' in help:
            return help.replace('%no_default', '')
        if ('%(default)' in help
            or action.default is None
            or action.default is False
            or action.default is argparse.SUPPRESS):
            return help
        return help + ' (default: %(default)s)'


def range_str(l):
    if len(l) == 0:
        return '<none>'
    p, str = None, ''
    for i in l:
        if p is not None and i == p[1]+1:
            p = p[0], i
            continue
        if p is not None:
            str += ('%d,' % p[0]) if p[0] == p[1] else ('%d-%d,' % p)
        p = (i,i)
    if p is not None:
        str += ('%d' % p[0]) if p[0] == p[1] else ('%d-%d' % p)
    return str

class TrackSet:

    class TrackIter:
        """Iterate over a TrackSet in physical <cyl,head> order."""
        def __init__(self, ts):
            l = []
            for c in ts.cyls:
                for h in ts.heads:
                    pc = c//-ts.step if ts.step < 0 else c*ts.step
                    pc += ts.h_off[h]
                    ph = 1-h if ts.hswap else h
                    l.append((pc, ph, c, h))
            l.sort()
            self.l = iter(l)
        def __next__(self):
            (self.physical_cyl, self.physical_head,
             self.cyl, self.head) = next(self.l)
            return self
    
    def __init__(self, trackspec):
        self.cyls = list()
        self.heads = list()
        self.h_off = [0]*2
        self.step = 1
        self.hswap = False
        self.trackspec = ''
        self.update_from_trackspec(trackspec)

    def update_from_trackspec(self, trackspec):
        """Update a TrackSet based on a trackspec."""
        self.trackspec += trackspec
        for x in trackspec.split(':'):
            if x == 'hswap':
                self.hswap = True
                continue
            k,v = x.split('=')
            if k == 'c':
                cyls = [False]*100
                for crange in v.split(','):
                    m = re.match('(\d\d?)(-(\d\d?)(/(\d))?)?$', crange)
                    if m is None: raise ValueError()
                    if m.group(3) is None:
                        s,e,step = int(m.group(1)), int(m.group(1)), 1
                    else:
                        s,e,step = int(m.group(1)), int(m.group(3)), 1
                        if m.group(5) is not None:
                            step = int(m.group(5))
                    for c in range(s, e+1, step):
                        cyls[c] = True
                self.cyls = []
                for c in range(len(cyls)):
                    if cyls[c]: self.cyls.append(c)
            elif k == 'h':
                heads = [False]*2
                for hrange in v.split(','):
                    m = re.match('([01])(-([01]))?$', hrange)
                    if m is None: raise ValueError()
                    if m.group(3) is None:
                        s,e = int(m.group(1)), int(m.group(1))
                    else:
                        s,e = int(m.group(1)), int(m.group(3))
                    for h in range(s, e+1):
                        heads[h] = True
                self.heads = []
                for h in range(len(heads)):
                    if heads[h]: self.heads.append(h)
            elif re.match('h[01].off$', k):
                h = int(re.match('h([01]).off$', k).group(1))
                m = re.match('([+-][\d])$', v)
                if m is None: raise ValueError()
                self.h_off[h] = int(m.group(1))
            elif k == 'step':
                m = re.match('1/(\d)$', v)
                self.step = -int(m.group(1)) if m is not None else int(v)
            else:
                print(k,v)
                raise ValueError()
        
    def __str__(self):
        s = 'c=%s' % range_str(self.cyls)
        s += ':h=%s' % range_str(self.heads)
        for i in range(len(self.h_off)):
            x = self.h_off[i]
            if x != 0:
                s += ':h%d.off=%s%d' % (i, '+' if x >= 0 else '', x)
        if self.step != 1:
            s += ':step=' + (('1/%d' % -self.step) if self.step < 0
                             else ('%d' % self.step))
        if self.hswap: s += ':hswap'
        return s

    def __iter__(self):
        return self.TrackIter(self)


image_types = OrderedDict(
    { '.adf': 'ADF',
      '.ads': ('ADS','acorn'),
      '.adm': ('ADM','acorn'),
      '.adl': ('ADL','acorn'),
      '.d81': 'D81',
      '.dsd': ('DSD','acorn'),
      '.dsk': 'EDSK',
      '.hfe': 'HFE',
      '.ima': 'IMG',
      '.img': 'IMG',
      '.ipf': 'IPF',
      '.raw': 'KryoFlux',
      '.sf7': 'SF7',
      '.scp': 'SCP',
      '.ssd': ('SSD','acorn'),
      '.st' : 'IMG' })

def get_image_class(name):
    if os.path.isdir(name):
        typespec = 'KryoFlux'
    else:
        _, ext = os.path.splitext(name)
        error.check(ext.lower() in image_types,
                    """\
%s: Unrecognised file suffix '%s'
Known suffixes: %s"""
                    % (name, ext, ', '.join(image_types)))
        typespec = image_types[ext.lower()]
    if isinstance(typespec, tuple):
        typename, classname = typespec
    else:
        typename, classname = typespec, typespec.lower()
    mod = importlib.import_module('fluxvis.greaseweazle.image.' + classname)
    return mod.__dict__[typename]


def with_drive_selected(fn, usb, args, *_args, **_kwargs):
    usb.set_bus_type(args.drive[0])
    try:
        usb.drive_select(args.drive[1])
        usb.drive_motor(args.drive[1], _kwargs.pop('motor', True))
        fn(usb, args, *_args, **_kwargs)
    except KeyboardInterrupt:
        print()
        usb.reset()
        raise
    finally:
        usb.drive_motor(args.drive[1], False)
        usb.drive_deselect()


def valid_ser_id(ser_id):
    return ser_id and ser_id.upper().startswith("GW")



# Local variables:
# python-indent: 4
# End:
