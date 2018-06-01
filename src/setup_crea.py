# -*- coding: utf-8 -*-

import os
import shutil
import struct


bits = struct.calcsize("P") * 8


#---Mueve el direrctorio dist a install/64 ó install/32
path = os.path.dirname(os.path.abspath(__file__))
path_dist = os.path.join(path, "dist")
if bits == 64:
    path_inst = os.path.join(path, "install", "64")
else:
    path_inst = os.path.join(path, "install", "32")

if os.path.exists(path_inst):
    shutil.rmtree(path_inst)

if os.path.exists(path_dist):
    shutil.move(path_dist, path_inst)


#---Crea fichero nsi final
data = install = unistall = ""
path64 = os.path.join(path, "install", "64")
for fic in os.listdir(path64):
    install += '        File "64\%s"\n' % fic
    unistall += '       Delete "$INSTDIR\%s"\n' %fic

nsi_org = os.path.join(path, "original.nsi")
with open(nsi_org, 'rb') as f:
    data = f.read()

data = data.replace('__FIC_INSTALL__', install)
data = data.replace('__FIC_UNINSTALL__', unistall)

nsi_des = os.path.join(path, 'install', 'pgimporta.nsi')
with open(nsi_des, 'wb') as f:
    f.write(data)

