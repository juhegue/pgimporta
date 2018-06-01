# -*- coding: utf-8 -*-

import os
import pickle
import wx


def get_datos(db, tabla):
    campos_tabla = db.get_campos(tabla)
    campos_sql = []
    campos = []
    for c in campos_tabla:
        tipo = c[1]
        if tipo != "bytea":
            campos_sql.append('"%s"' % c[0])
            campos.append(c[0])

    cursor = None
    if campos_sql:
        sql = "SELECT %s FROM %s" % (",".join(campos_sql), tabla)
        cursor = db.ejecuta_many(sql)

    data = []
    pkey = []
    if cursor:
        for n, reg in enumerate(db.resul_iter(cursor)):
            if n % 100 == 0: wx.Yield()
            data.append(reg)

        pkeys = db.get_primary_key(tabla)
        if pkeys:
            for k in pkeys:
                pkey.append(k[0])
        else:
            for c in campos:
                pkey.append(c)

    return data, campos, pkey


def exporta_tabla(path, db, tabla):
    data, campos, pkeys = get_datos(db, tabla)
    datos = dict()
    for reg in data:
        valores = []
        keys = []
        for i, c in enumerate(reg):
            nom = campos[i]
            valores.append(c)
            if nom in pkeys:
                keys.append(c)
        datos[tuple(keys)] = valores

    fichero = os.path.join(path, tabla + ".pkl")
    try:
        with open(fichero, 'wb') as f:
            pickle.dump(datos, f)

    except IOError, e:
        return "%s\n\n%s" % (e, fichero)

    except TypeError, e:
        return "%s\n\n%s" % (e, fichero)

    return None


def compara_tabla(resultado, fichero, db, tabla):
    data, campos, pkeys = get_datos(db, tabla)
    if db.error:
        return db.error

    tmp = dict()

    try:
        with open(fichero, 'rb') as f:
            datos = pickle.load(f)
    except IOError, e:
        return "%s\n\n%s" % (e, fichero)

    for reg in data:
        valores = []
        keys = []
        for i, c in enumerate(reg):
            nom = campos[i]
            valores.append(c)
            if nom in pkeys:
                keys.append(c)

        key = tuple(keys)
        if key in datos:
            for i, d in enumerate(datos[key]):
                if d != reg[i]:
                    # tmp[key] = ["MODI", datos[key], valores]
                    tmp[key] = ["MODI", valores, datos[key]]
                    break
            del datos[key]
        else:
            #cuando una tabla no tiene pkey, puede que el registro este duplicado (y se ha borrado)
            if key in tmp:
                for i, d in enumerate(tmp[key][1]):
                    if d != reg[i]:
                        # tmp[key] = ["MODI", datos[key], valores]
                        tmp[key] = ["MODI", valores, datos[key]]
                        break
            else:
                tmp[key] = []
                tmp[key] = ["NUEVO", [], valores]

    for d in datos.items():
        tmp[d[0]] = []
        tmp[d[0]] = ["BORRA", d[1], []]

    if tmp:
        resultado[tabla] = tmp

    return None

if __name__ == '__main__':
    from dbpostgres import DbPostgres

    db = DbPostgres()
    db.conecta("localhost", 5432, "openerp", "openerp", "prueba")

    #print exporta_tabla("/home/juan/workspace/openerp/pgImportar/src/bd", db, "account_tax")
    datos = dict()
    print compara_tabla(datos, "/home/juan/workspace/openerp/pgImportar/src/bd/account_tax.pkl", db, "account_tax")
    print "=>", datos
