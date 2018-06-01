# -*- coding: utf-8 -*-

import json
from constantes import *


class Pgi(object):
    def __init__(self, data=None):
        self.data = data
        self.version = None
        self.conexion = None
        self.valor_fijo = list()
        self.sql_ini = list()
        self.fichero_csv = None
        self.sql_reg = list()
        self.id_insert = list()
        self.campo_def = list()
        self.filtros = dict()
        self.campo_filtros = dict()
        self.nombre = None
        self.campo_reg = list()
        self.notas_tabla = list()
        self.notas = None
        self.condicion_tabla = dict()
        self.codigo_inicial = list()
        self.codigo_final = list()
        if self.data:
            self.procesa()

    def set_data(self, data):
        self.data = data
        self.procesa()

    def set_fichero(self, fichero):
        with open(fichero, 'r') as f:
            self.data = json.load(f)
        self.procesa()

    def procesa(self):
        self.version = None
        self.conexion = None
        self.valor_fijo = list()
        self.sql_ini = list()
        self.fichero_csv = None
        self.sql_reg = list()
        self.id_insert = list()
        self.campo_def = list()
        self.filtros = dict()
        self.campo_filtros = dict()
        self.nombre = None
        self.campo_reg = list()
        self.notas_tabla = list()
        self.notas = None
        self.condicion_tabla = dict()
        for k, v in sorted(self.data.iteritems()):
            if k == VERSION:
                self.version = v

            if k == CONEXION:
                self.conexion = v

            if k.find(VALOR_FIJO) == 0:
                self.valor_fijo.append(v)

            if k.find(SQL_INI) == 0:
                self.sql_ini.append(v)

            if k == FICHERO_CSV:
                self.fichero_csv = v

            if k.find(SQL_REG) == 0:
                self.sql_reg.append(v)

            if k.find(ID_INSERT) == 0:
                self.id_insert.append(v)

            if k.find(CAMPO_DEF) == 0:
                self.campo_def.append(v)

            if k == FILTROS:
                self.filtros = v.copy()

            if k == CAMPO_FILTROS:
                self.campo_filtros = v.copy()

            if k == NOMBRE:
                self.nombre = v

            if k.find(CAMPO_REG) == 0:
                self.campo_reg.append(v)

            if k.find(CODIGO_INICIAL) == 0:
                self.codigo_inicial.append(v)

            if k.find(CODIGO_FINAL) == 0:
                self.codigo_final.append(v)

            if k.find(NOTAS_TABLA) == 0:
                self.notas_tabla.append(v)

            if k == NOTAS:
                self.notas = v

            if k == CONDICION_TABLA:
                self.condicion_tabla = v.copy()

    def get_campos_csv(self):
        """
        Retorna una lista con los campos del csv
        :return: list()
        """
        campos = []
        if FICHERO_CSV in self.data and "campos" in self.data[FICHERO_CSV]:
            campos = self.data[FICHERO_CSV]["campos"][:]
            for data in self.campo_def:
                nombre = data["nombre"]
                campos.append(nombre)
        return campos

    def get_campos_csv_usados(self):
        """
        Retorna una lista con los campos del csv usados
        :return: list()
        """
        cam_csv = self.get_campos_csv()
        val_csv = list()
        valores = list()
        usados = dict()

        for data in self.sql_reg:
            valor = data["sql"]
            val_csv.append(valor)

        for tabla, campos, keys in self.id_insert:
            for campo, asignado in campos:
                if asignado:
                    val_csv.append(asignado)

        for data in self.campo_def:
            valor = data["valor"]
            valores.append(valor)

        for data in self.campo_reg:
            valor = data["valor"]
            val_csv.append(valor)

        for data in self.codigo_inicial:
            valor = data["valor"]
            val_csv.append(valor)

        for data in self.codigo_final:
            valor = data["valor"]
            val_csv.append(valor)

        for valor in self.condicion_tabla.itervalues():
            val_csv.append(valor["condicion"])

        for campo in sorted(cam_csv, reverse=True):
            a=1+1
            for n, v in enumerate(val_csv):
                csv = "@csv.%s" % campo
                if v == csv:
                #if v.find(csv) >= 0:
                    usados[campo] = campo
                    val_csv[n] = v.replace(csv, "")
            for n, v in enumerate(valores):
                if v == campo:
                #if v.find(campo) >= 0:
                    usados[campo] = campo
                    val_csv[n] = v.replace(campo, "")

        return usados.keys()

    def get_nombres(self):
        """
        Retorna la lista de los nombres de campos y sql's
        :return: list()
        """
        nombres = list()
        for k, v in sorted(self.data.iteritems()):
            if k.find(CAMPO_DEF) == 0:
                actual = self.data[k]['nombre']
                nombres.append("csv.%s" % actual)
            elif k.find(VALOR_FIJO) == 0:
                actual = self.data[k]['nombre']
                nombres.append(actual)
            elif k.find(ID_INSERT) == 0:
                actual = v[0]
                nombres.append(actual)
            elif k.find(SQL_INI) == 0:
                actual = self.data[k]['nombre']
                nombres.append(actual)
            elif k.find(SQL_REG) == 0:
                actual = self.data[k]['nombre']
                nombres.append(actual)
            elif k.find(FICHERO_CSV) == 0:
                for actual in self.data[k]['campos']:
                    nombres.append("csv.%s" % actual)
            elif k.find(CAMPO_REG) == 0:
                actual = self.data[k]['nombre']
                nombres.append(actual)
            elif k.find(CODIGO_INICIAL) == 0:
                actual = self.data[k]['nombre']
                nombres.append(actual)
            elif k.find(CODIGO_FINAL) == 0:
                actual = self.data[k]['nombre']
                nombres.append(actual)
        return nombres