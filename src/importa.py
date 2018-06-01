# -*- coding: utf-8 -*-

import sys
import os
import time
import copy
import traceback
from odict import odict
from csvunicode import UnicodeReader
from dbpostgres import DbPostgres
from parse_select import parse_select
from constantes import *
import codigo
import util


class Log(object):
    def __init__(self, fic_log, tipo_log, titulo):
        self.data = dict()
        self.tipo = tipo_log
        self.fic = open(fic_log, 'w') if fic_log else None
        self.__write("INICIO " + titulo)

    def __write(self, titulo, txt=""):
        if self.fic:
            hora = time.strftime("%H:%M:%S")
            txt = "%s:%s:\t%s\n" % (hora, titulo, txt)
            self.fic.write(txt)

    def __del__(self):
        if self.fic:
            self.__write("FINAL")
            for k, v in self.data.iteritems():
                self.fic.write("%s %s registros \n" % (k, v))
            self.fic.close()

    def write(self, titulo, txt="", error=""):
        if self.tipo == 1:  # Detallado
            self.__write(titulo, txt)
            if error:
                self.__write("ERROR", error)

    def resumen(self, tabla):
        if tabla in self.data:
            self.data[tabla] += 1
        else:
            self.data[tabla] = 1


class Sql(object):
    def __init__(self, fic_log, tipo_log):
        self.data = dict()
        if tipo_log:
            self.fic = open(fic_log, 'w') if fic_log else None
        else:
            self.fic = None

    def write(self, txt):
        if self.fic:
            self.fic.write("%s\n" % txt)

    def __del__(self):
        if self.fic:
            self.fic.close()


class Importa(object):
    def __init__(self, fic_log=None, fic_sql=None, tipo_log=0, tipo_sql=0):
        self.__contador = 0
        self.__error = None
        self.__cam_valor = odict()
        self.__log = None
        self.__sql = None
        self.__ficlog = fic_log
        self.__ficsql = fic_sql
        self.__tipo_log = tipo_log
        self.__tipo_sql = tipo_sql
        self.db = DbPostgres()
        self.db.auto_commit = False
        self.__cam_filtros = dict()

    @property
    def error(self):
        return self.__error

    @staticmethod
    def __valor2unicode(valor):
        if type(valor) is str:
            valor = valor.decode("utf-8")
        elif type(valor) is not unicode:
            valor = unicode(valor)
        return valor

    def __asigna_campos(self, txt, dic=None):
        if not dic:
            dic = self.__cam_valor
        #orden inverso, para que reemplace primero las cadenas mas largas
        #ya que estas pueden contener a las mas pequeñas
        for k in sorted(dic.keys(), reverse=True):
            v = dic[k]
            txt = txt.replace(k, self.__valor2unicode(v))

        txt = txt.replace("'None'", "NULL")
        return txt

    def __asigna_campos_code(self, txt, dic):
        #orden inverso, para que reemplace primero las cadenas mas largas
        #ya que estas pueden contener a las mas pequeñas
        for k in sorted(dic.keys(), reverse=True):
            v = dic[k]
            if isinstance(v, str) or isinstance(v, unicode):
                v = v.replace("''", "\\'")
            txt = txt.replace(k, self.__valor2unicode(v))

      #  txt = txt.replace("'None'", "NULL")
        return txt

    def __set_campo(self, nombre, valor, dic=None):
        for k, v in self.__cam_filtros.iteritems():
            if nombre == "csv." + k:
                for f in v:
                    try:
                        valor = self.__filtros[f](valor)
                        self.__log.write("Filtro %s" % k, valor)
                    except:
                        exc_type, exc_value, exc_traceback = sys.exc_info()
                        exc = traceback.format_exception(exc_type, exc_value, exc_traceback)
                        exc.insert(0, "Filtro %s, campo %s%s" % (f, k, os.linesep))
                        exc.insert(0, "*** Linea csv:%s ***%s" % (self.__contador, os.linesep))
                        err = os.linesep.join(exc)
                        raise Exception(err)

        if type(valor) == unicode or type(valor) == str:
            valor = valor.replace("'", "''")  # Escape de ' (comillas simple)

        if type(dic) == dict:
            dic["@"+nombre] = valor
        else:
            self.__cam_valor["@"+nombre] = valor

    def ejecuta(self, data_org, commit, fun_actualiza=None, fun_param=None, maximo=None):
        titulo = "Actualizar" if commit else "Prueba"
        self.__log = Log(self.__ficlog, self.__tipo_log, titulo)
        self.__sql = Sql(self.__ficsql, self.__tipo_sql)
        self.__error = None
        self.__cam_valor = dict()
        msg = ""

        data = copy.deepcopy(data_org)
        try:
            if util.versiontuple(data["Version"]) < "0.1.1":
                err = u"Versión incorrecta [%s], actual la [%s]" % (data["Version"], NVERSION)
                raise Exception(err)

            codigo.inicia()
            self.__conecta(data)
            inc = self.__codigo_inicial(data, maximo)
            self.__csv(data)
            self.__fijos(data)
            self.__sql_inicial(data)
            self.__sql_por_registro(data)
            self.__tablas_insert(data)
            self.__campos_definidos(data)
            self.__filtros(data)
            self.__recorre_csv(data, fun_actualiza, fun_param, maximo, inc)

        except KeyError, e:
            self.__error = u"KeyError en valor %s" % e

        except Exception, e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            self.__error = os.linesep.join(exc_value)
            # este da el número de línea
            #  exc = traceback.format_exception(exc_type, exc_value, exc_traceback)
            #  self.__error = os.linesep.join(exc)
        finally:
            if self.__error:
                self.db.actualiza(False)
            else:
                self.db.actualiza(commit)
                try:
                    self.__codigo_final(data)
                except Exception, e:
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    self.__error = os.linesep.join(exc_value)

            self.db.close()
            del self.__log
            del self.__sql

    def __codigo_inicial(self, data, maximo):
        fic_csv = data[FICHERO_CSV]["fichero"]

        for k, v in sorted(data.iteritems()):
            if k.find(CODIGO_INICIAL) == 0:
                code = data[k]["valor"]
                nombre = data[k]["nombre"]
                data, err = codigo.codigo(code, data, self.db)
                if err:
                    self.__log.write(u"Código inicial %s" % nombre, "error", err.replace("\n", " "))
                    raise Exception(u"Código inicial [%s]:\n%s" % (nombre, err))
                else:
                    self.__log.write(u"Código inicial %s" % nombre, "ok")

        fic_nuevo = data[FICHERO_CSV]["fichero"]
        if fic_csv != fic_nuevo:
            registros = open(fic_nuevo).read().count('\n')
        else:
            registros = maximo

        return float(maximo) / float(registros) if maximo else 1

    def __codigo_final(self, data):
        for k, v in sorted(data.iteritems()):
            if k.find(CODIGO_FINAL) == 0:
                code = data[k]["valor"]
                nombre = data[k]["nombre"]
                data, err = codigo.codigo(code, data, self.db)
                if err:
                    self.__log.write(u"Código final %s" % nombre, "error", err.replace("\n", " "))
                    raise Exception(u"Código final [%s]:\n%s" % (nombre, err))
                else:
                    self.__log.write(u"Código final %s" % nombre, "ok")

    def __conecta(self, data):
        try:
            host = data[CONEXION]["host"]
            puerto = data[CONEXION]["puerto"]
            usuario = data[CONEXION]["usuario"]
            clave = data[CONEXION]["clave"]
            database = data[CONEXION]["database"]
            self.db.conecta(host, puerto, usuario, clave, database)
            if self.db.error:
                raise Exception(self.db.error)
        except KeyError, e:
            err = u"KeyError en [%s] valor %s" % (CONEXION, e)
            raise Exception(err)

    def __csv(self, data):
        try:
            self.csv_fichero = data[FICHERO_CSV]["fichero"]
            self.csv_nom1linea = data[FICHERO_CSV]["nombres1"]
            self.csv_delimitador = str(data[FICHERO_CSV]["delimitador"])
            self.csv_campos = data[FICHERO_CSV]["campos"]
            self.csv_encode = data[FICHERO_CSV]["encode"]
            if self.csv_delimitador == "tab":
                self.csv_delimitador = chr(9)
        except KeyError, e:
            err = u"KeyError en [%s] valor %s" % (FICHERO_CSV, e)
            raise Exception(err)

    def __fijos(self, data):
        try:
            for k, v in sorted(data.iteritems()):
                if k.find(VALOR_FIJO) == 0:
                    nombre = v["nombre"]
                    valor = v["valor"]
                    self.__set_campo(nombre, valor)
        except KeyError, e:
            err = u"KeyError en [%s] valor %s" % (VALOR_FIJO, e)
            raise Exception(err)

    def __sql_inicial(self, data):
        try:
            for k, v in sorted(data.iteritems()):
                if k.find(SQL_INI) == 0 and v["sql"]:
                    nom = v["nombre"]
                    cam = v["campos"]
                    sql = v["sql"]
                    continuar = v["continuar"]  # 0=siempre 1=se cumnple 2=no se cumple

                    tablas, campos, sql = parse_select(self.db, sql)
                    sql = self.__asigna_campos(sql)

                    data = self.db.ejecuta_one(sql)
                    self.__log.write("Inicial %s" % nom, sql, self.db.error)
                    self.__log.write("Retorna", data)
                    self.__sql.write(sql)
                    if self.db.error:
                        raise Exception(self.db.error + sql)
                    else:
                        if continuar == 1 and self.db.rowcount == 0:
                            err = "%s, No se cumple: %s" % (SQL_INI, nom)
                            raise Exception(err)

                        if continuar == 2 and self.db.rowcount == 1:
                            err = "%s, Se cumple: %s" % (SQL_INI, nom)
                            raise Exception(err)

                        if cam:
                            if data:
                                for i, c in enumerate(campos):
                                    nombre = "%s.%s" % (nom, c)
                                    valor = data[i]
                                    self.__set_campo(nombre, valor)
                            else:
                                for c in campos:
                                    nombre = "%s.%s" % (nom, c)
                                    valor = cam[c]
                                    self.__set_campo(nombre, valor)
        except KeyError, e:
            err = u"KeyError en [%s] valor %s" % (SQL_INI, e)
            raise Exception(err)

        except TypeError, e:
            err = "TypeError en [%s]: %s" % (SQL_INI, e)
            raise Exception(err)

    def __tablas_insert(self, data):
        self.__insert = []
        try:
            for k, v in sorted(data.iteritems()):
                if k.find(ID_INSERT) == 0:
                    tabla = v[0]
                    cam_tabla = v[1]
                    cam_id = v[2]
                    nombres = []
                    valores = []
                    for c in cam_tabla:
                        nombre = c[0][0]
                        valor = c[1]
                        if valor is not None:
                            nombres.append(nombre)
                            valores.append(valor)
                    self.__insert.append([tabla, nombres, valores, cam_id])

        except AttributeError, e:
            err = u"AttributeError en [%s] valor %s" % (ID_INSERT, e)
            raise Exception(err)

        except KeyError, e:
            err = u"KeyError en [%s] valor %s" % (ID_INSERT, e)
            raise Exception(err)

    def __sql_por_registro(self, data):
        self.__por_registro = []
        try:
            for k, v in sorted(data.iteritems()):
                if k.find(SQL_REG) == 0:
                    nom = v["nombre"]
                    cam = v["campos"]
                    sql = v["sql"]
                    continuar = v["continuar"]  # 0=siempre 1=se cumnple 2=no se cumple
                    modificar = v["modificar"]  # True/False
                    eje_antes = v["ejecuta_antes"] if "ejecuta_antes" in v else False
                    ins_antes = v["insert_antes"] if "insert_antes" in v else None
                    tablas, campos, sql = parse_select(self.db, sql)
                    self.__por_registro.append([nom, cam, tablas, campos, sql, continuar, modificar, eje_antes, ins_antes])

        except KeyError, e:
            err = u"KeyError en [%s] valor %s" % (SQL_REG, e)
            raise Exception(err)

    def __campos_definidos(self, data):
        self.__funciones = None
        self.__cam_def = []
        try:
            for k, v in sorted(data.iteritems()):
                if k.find(CAMPO_DEF) == 0:
                    self.__cam_def.append([v["nombre"], v["valor"]])

            if self.__cam_def:
                self.__funciones, err = codigo.crea_modulo(self.__cam_def, data[FICHERO_CSV])
                if err:
                    raise Exception(err)

        except KeyError, e:
            err = u"KeyError en [%s] valor %s" % (CAMPO_DEF, e)
            raise Exception(err)

    def __filtros(self, data):
        self.__filtros = None
        self.__cam_filtros = data[CAMPO_FILTROS] if CAMPO_FILTROS in data else dict()
        if FILTROS in data:
            try:
                self.__filtros, err = codigo.crea_modulo_filtros(data[FILTROS])
                if err:
                    raise Exception(err)

            except KeyError, e:
                err = u"KeyError en [%s] valor %s" % (FILTROS, e)
                raise Exception(err)

    def __recorre_csv(self, data, fun_actualiza, fun_param, maximo, inc):
        try:
            ncam = len(self.csv_campos)
            with open(self.csv_fichero, 'rb') as f:
                for contador, cam_data in enumerate(UnicodeReader(f, encoding=self.csv_encode, delimiter=self.csv_delimitador, quotechar='"')):
                    self.__contador = contador
                    if fun_actualiza:
                        conta_act = contador*inc
                        if conta_act > maximo:
                            conta_act = maximo
                        (continua, skip) = fun_actualiza(fun_param, conta_act)
                        if not continua:
                            break

                    if contador == 0:
                        lon0 = len(cam_data)

                        if lon0 != ncam:
                            err = u"Error en fichero csv, campos definidos:[%d], campos en csv:[%d]" % (ncam, lon0)
                            raise Exception(err)

                        if self.csv_nom1linea:
                            continue

                    lon1 = len(cam_data)
                    if not lon1:
                        continue

                    cam_valor = self.__add_cam_definidos(contador, cam_data)

                    for i, c in enumerate(self.csv_campos):
                        nom = "csv.%s" % c
                        valor = cam_data[i]
                        self.__set_campo(nom, valor, cam_valor)

                    self.__log.write("Contador", contador)
                    self.__registro(cam_valor, data)
                    pass

        except IOError, e:
            err = "ERROR:%s:[%s]" % (e, self.csv_fichero)
            raise Exception(err)

        except TypeError, e:
            err = "ERROR:%s:[%s]" % (e, self.csv_fichero)
            raise Exception(err)

    def __add_cam_definidos(self, contador, cam_data):
        cam_copia = self.__cam_valor.copy()
        for c in self.__cam_def:
            try:
                valor = self.__funciones[c[0]](cam_data)
            except:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                exc = traceback.format_exception(exc_type, exc_value, exc_traceback)
                exc.insert(0, "*** Linea csv:%s ***%s" % (contador, os.linesep))
                err = os.linesep.join(exc)
                raise Exception(err)

            if type(valor) != unicode:
                valor = str(valor)

            nom = "csv.%s" % c[0]
            self.__set_campo(nom, valor, cam_copia)

        return cam_copia

    def __campos_registro(self, data, cam_valor):
        for k, v in sorted(data.iteritems()):
            if k.find(CAMPO_REG) == 0:
                nombre = v["nombre"]
                valor = v["valor"]
                code = self.__asigna_campos_code(valor, cam_valor)
                resul, error = codigo.exec_codigo(nombre, code, self.db)
                self.__set_campo(nombre, resul, cam_valor)
                self.__log.write("Campo %s" % nombre, resul, error)

    def __registro(self, cam_valor, pgi_data):
        tabla_modi = dict()

        def por_registro(reg):
            nom = reg[0]
            cam = reg[1]
            tablas = reg[2]
            campos = reg[3]
            sql = reg[4]
            continuar = reg[5]
            modificar = reg[6]

            # Quita el prefijo ??_ a la tabla en la sql
            if modificar:
                sql = sql.replace(tablas[0], tablas[0][3:], 1)

            sql = self.__asigna_campos(sql, cam_valor)
            data = self.db.ejecuta_one(sql)
            self.__log.write("Registro %s" % nom, sql, self.db.error)
            self.__log.write("Retorna", data)
            self.__sql.write(sql)
            if self.db.error:
                raise Exception(self.db.error + sql)
            else:
                if continuar == 1 and self.db.rowcount == 0:
                    return True
                if continuar == 2 and self.db.rowcount == 1:
                    return True

                if data:
                    for i, c in enumerate(campos):
                        nombre = "%s.%s" % (nom, c)
                        valor = data[i]
                        self.__set_campo(nombre, valor, cam_valor)
                else:
                    for i, c in enumerate(campos):
                        nombre = "%s.%s" % (nom, c)
                        valor = cam[c]
                        self.__set_campo(nombre, valor, cam_valor)

                if data and cam and modificar:
                    tabla_modi[tablas[0]] = [campos, data]
            return False

        # meto en una lista todas las tablas que hacen el insert
        insert = []
        for ins in self.__insert:
            insert.append(ins[0])

        # compruebo si alguna tabla "por registro" esta en la lista de las insert
        # si está la guardo en un diccionario para ejecutarla justo antes del insert
        dic_por_registro = dict()
        for reg in self.__por_registro:
            tabla = reg[2]
            if tabla and tabla[0] in insert:
                dic_por_registro[tabla[0]] = reg
            elif not reg[7]:    # si no se ejecuta justo antes
                if por_registro(reg):
                    return

        primero = True
        for ins in self.__insert:
            if primero:
                primero = False
                self.__campos_registro(pgi_data, cam_valor)

            for reg in self.__por_registro:  # las que se ejecutan justo antes
                if reg[7] and reg[8] == ins[0]:
                    if por_registro(reg):
                        return

            tabla_prefijo = ins[0]
            tabla = ins[0][3:]
            campos = ins[1]
            valores = ins[2]
            ids = ins[3]

            # la condición de la tabla
            if CONDICION_TABLA in pgi_data and tabla_prefijo in pgi_data[CONDICION_TABLA]:
                condicion = pgi_data[CONDICION_TABLA][tabla_prefijo]["condicion"]
                continua = pgi_data[CONDICION_TABLA][tabla_prefijo]["continua"]
                code = self.__asigna_campos_code(condicion, cam_valor)
                resul, error = codigo.exec_funcion(code, self.db)
                self.__log.write(u"Condición %s" % tabla_prefijo, resul, error)
                if resul is True:
                    if continua == 0:
                        continue
                    if continua == 1:
                        break

            # ejecuta la tabla "por registro" antes del insert, porque igual hay que hacer un update
            if tabla_prefijo in dic_por_registro:
                if por_registro(dic_por_registro[tabla_prefijo]):
                    return

            cam = []
            val = []
            for i in range(0, len(campos)):
                valor = valores[i]
                if valor is not None and valor != "null":
                    cam.append('"%s"' % campos[i])
                    val.append("'%s'" % self.__valor2unicode(valor))

            if tabla_prefijo in tabla_modi:
                sql = self.__crea_update(tabla, cam, val, tabla_modi[tabla_prefijo][0], tabla_modi[tabla_prefijo][1], ids)
                sql = self.__asigna_campos(sql, cam_valor)
                data = self.db.ejecuta_one(sql)
                self.__log.resumen("UPDATE %s" % tabla)
                self.__log.write("Update %s" % tabla_prefijo, sql, self.db.error)
                self.__log.write("Retorna", data)
                self.__sql.write(sql)
                if self.db.error:
                    raise Exception(self.db.error + sql)
            else:
                if ids:
                    sql = u'INSERT INTO "%s" (%s) VALUES (%s) RETURNING %s' % (tabla, ",".join(cam), ",".join(val), ",".join(ids))
                else:
                    sql = u'INSERT INTO "%s" (%s) VALUES (%s)' % (tabla, ",".join(cam), ",".join(val))
                sql = self.__asigna_campos(sql, cam_valor)
                data = self.db.ejecuta_one(sql)
                self.__log.resumen("INSERT %s" % tabla)
                self.__log.write("Insert %s" % tabla_prefijo, sql, self.db.error)
                self.__log.write("Retorna", data)
                self.__sql.write(sql)
                if self.db.error:
                    raise Exception(self.db.error + sql)

            for i, id in enumerate(ids):
                valor = data[i]
                nombre = "%s.%s" % (tabla_prefijo, id)
                self.__set_campo(nombre, valor, cam_valor)

            self.__campos_registro(pgi_data, cam_valor)

    @staticmethod
    def __crea_update(tabla, campos, valores, campos_condi, valores_condi, ids):
        datos = condicion = ""
        for i, c in enumerate(campos):
            if datos:
                datos += ", %s=%s" % (c, valores[i])
            else:
                datos = "%s=%s" % (c, valores[i])

        for i, c in enumerate(campos_condi):
            if condicion:
                condicion += "AND '%s'='%s'" % (c, valores_condi[i])
            else:
                condicion = "\"%s\"='%s'" % (c, valores_condi[i])

        if ids:
            return "UPDATE %s SET %s WHERE %s RETURNING %s" % (tabla, datos, condicion, ",".join(ids))

        return "UPDATE %s SET %s WHERE %s" % (tabla, datos, condicion)