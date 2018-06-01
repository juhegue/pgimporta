# -*- coding: utf-8 -*-

"""
Importar datos a PostgreSQL (Created on 21/04/2015)
@author: juan hevilla guerrero

SINOPSIS
    pgimporta.py   [-f --fichero] [-c --csv] [-d -db] [-p probar] [-h --help]

OPCIONES
    -f  fichero.pgi
    -c  datos fichero csv: fichero,nombres1linea(1=si,0=no),encode,delimitador
    -d  datos database: host,database,puerto,usuario,clave
    -p  solo probar (no actualiza la BD)
    -l  fichero log/sql
    -t  tipo log (0 defecto / 1 detallado / 2 sql / 3 detallado y sql)
    -h  Muestra ayuda
"""

import os
import sys
import getopt
import json
import logging


class StreamToLogger(object):
    """
    Fake file-like stream object that redirects writes to a logger instance.
    """
    def __init__(self, logger, log_level=logging.INFO):
        self.logger = logger
        self.log_level = log_level
        self.linebuf = ''

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.log_level, line.rstrip())


if __name__ == '__main__':

    logging.basicConfig(
        level=logging.DEBUG,
        #format='%(asctime)s:%(levelname)s:%(name)s:%(message)s',
        format='%(levelname)s:%(message)s',
        filename="pgimporta.log",
        filemode='w'  # 'a' para añadir
    )

    stdout_logger = logging.getLogger('STDOUT')
    sl = StreamToLogger(stdout_logger, logging.INFO)
    sys.stdout = sl

    stderr_logger = logging.getLogger('STDERR')
    sl = StreamToLogger(stderr_logger, logging.ERROR)
    sys.stderr = sl

    directorio = os.getcwd()
    fichero = db = csv = probar = False
    tipo_log = tipo_sql = 0
    log = sql = None
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hf:c:d:l:t:p", ["help", "fichero=", "csv=", "db=", "log=", "tipo=", "probar"])
    except getopt.error, msg:
        print msg
        print "Para ayuda usar --help"
        sys.exit(2)

    for o, c in opts:
        if o in ("-h", "--help"):
            print __doc__
            sys.exit(0)
        if o in ("-f", "--fichero"):
            fichero = c
        if o in ("-c", "--csv"):
            csv = c
        if o in ("-d", "--db"):
            db = c
        if o in ("-l", "--log"):
            log = "%s.log" % c
            sql = "%s.sql" % c
        if o in ("-t", "--tipo"):
            if c == "1":
                tipo_log = 1
            elif c == "2":
                tipo_sql = 1
            elif c == "3":
                tipo_log = tipo_sql = 1
        if o in ("-p", "--probar"):
            probar = True

    if fichero:
        try:
            with open(fichero, 'r') as f:
                data = json.load(f)

            if data:
                import importa
                from constantes import *

                if db:
                    db = db.split(",")
                    lon = len(db)
                    data[CONEXION]["host"] = db[0]
                    if lon > 1:
                        data[CONEXION]["database"] = db[1]
                    if lon > 2:
                        data[CONEXION]["puerto"] = db[2]
                    if lon > 3:
                        data[CONEXION]["usuario"] = db[3]
                    if lon > 4:
                        data[CONEXION]["clave"] = db[4]

                if csv:
                    csv = csv.split(",")
                    lon = len(csv)
                    data[FICHERO_CSV]["fichero"] = csv[0]
                    if lon > 1:
                        if csv[1] == 0:
                            data[FICHERO_CSV]["nombres1"] = False
                        else:
                            data[FICHERO_CSV]["nombres1"] = True
                    if lon > 2:
                        data[FICHERO_CSV]["encode"] = csv[2]
                    if lon > 3:
                        if lon > 4:
                            data[FICHERO_CSV]["delimitador"] = ","
                        else:
                            data[FICHERO_CSV]["delimitador"] = csv[3]

        except IOError, e:
            print "ERROR:%s" % e
            sys.exit(1)

        except ValueError, e:
            print "ERROR:%s" % e
            sys.exit(2)

        if data:
            imp = importa.Importa(log, sql, tipo_log, tipo_sql)
            imp.ejecuta(data, not probar)
            if imp.error:
                print imp.error
            else:
                print "Prueba OK" if probar else "OK"

    else:
        import wxmain
        wxmain.main()
