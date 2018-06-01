# -*- coding: utf-8 -*-

from distutils.core import setup
import py2exe
import struct
from constantes import *

bits = struct.calcsize("P") * 8
if bits == 64:
    bundle_files = 3
else:
    bundle_files = 1


class Target(object):
    """ A simple class that holds information on our executable file. """
    def __init__(self, **kw):
        """ Default class constructor. Update as you need. """
        self.__dict__.update(kw)

includes = []

excludes = ['_gtkagg', '_tkagg', 'bsddb', 'curses', 'email', 'pywin.debugger',
            'pywin.debugger.dbgcon', 'pywin.dialogs', 'tcl',
            'Tkconstants', 'Tkinter', 
            'Carbon', 'Carbon.Files',
            'netbios', 'simplejson', 'win32api', 'win32con', 'win32pipe', 'win32wnet']

packages = []

dll_excludes = ['libgdk-win32-2.0-0.dll', 'libgobject-2.0-0.dll', 'tcl84.dll',
                'tk84.dll', 'msvcp90.dll']

icon_resources = [(1, 'pgimporta.ico')]
bitmap_resources = []
other_resources = []

windows_target = Target(
    script="pgimporta.py",
    icon_resources=icon_resources,
    bitmap_resources=bitmap_resources,
    other_resources=other_resources,
    dest_base="pgimporta",
    version=NVERSION,
    company_name=NOM_COMPANY,
    copyright=COPYRIGHT,
    name=APLICACION)

setup(
    options={"py2exe": {"compressed": 2,
                        "optimize": 2,
                        "includes": includes,
                        "excludes": excludes,
                        "packages": packages,
                        "dll_excludes": dll_excludes,
                        "bundle_files": bundle_files,
                        "dist_dir": "dist",
                        "xref": False,
                        "skip_archive": False,
                        "ascii": False,
                        "custom_boot_script": ''}},

    windows=[windows_target],
    data_files=["pgimporta.ico"],

    zipfile=None,

    name=APLICACION,
    version=NVERSION,
    description=DESCRIPCION,
    author=AUTOR,
    author_email=AUTOR_EMAIL,
    maintainer=AUTOR,
    maintainer_email=AUTOR_EMAIL,
    url=URL_COMPANY,
)

#Ejecutar como: python setup.py py2exe