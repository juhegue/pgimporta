# -*- coding: utf-8 -*-

import sys
import imp
import traceback
from float_utils import *


_global = None


def __x():   # para que se cargue el modulo float_utils
    float_round(1, 2)


def inicia():
    global _global
    _global = None


def error(e, inc):
    exc_type, exc_value, exc_traceback = sys.exc_info()
    exc = traceback.format_exception(exc_type, exc_value, exc_traceback)
    del (exc_type, exc_value, exc_traceback)

    # Quita la línea que tiene el nombre de este módulo
    for i, x in enumerate(exc):
        if "codigo.py" in x:
            del exc[i]
            break

    # Modifica la líea con el error
    for i, x in enumerate(exc):
        pos = x.find(" line ")
        if pos > 0:
            nume = x[pos + 6:].strip()
            try:
                lin = int(nume) - inc
                txt = x[:pos + 6]
                exc[i] = "%s %s\n" % (txt, lin)
            except:
                pass

    # err = os.linesep.join(exc) -> le mete un retorno de carro más
    err = "".join(exc)
    return err


# definir campo y filtro
def evalua_codigo(nombre, code, campos, valores):
    err = None
    modulo = imp.new_module('modulo')

    for i, c in enumerate(campos):
        setattr(modulo, c, valores[i])

    try:
        exec code in modulo.__dict__
        try:
            modulo.__dict__[nombre]
        except:
            err = "Falta asignar el nombre del campo"
    except Exception as e:
        if type(e) != Exception:
            err = error(e, 0)
    return err


# definir condición
def check_funcion(code, db):
    global _global
    modulo = imp.new_module('modulo')
    setattr(modulo, "_db", db)
    setattr(modulo, "_global", _global)

    try:
        funcion = "def f():\n"
        funcion += " global _global\n"
        for linea in code.split("\n"):
            funcion += " %s\n" % linea

        exec funcion in modulo.__dict__

    except SyntaxError as e:
        return error(e, 2)
    except:
        pass


# filtros definidos
def crea_modulo_filtros(filtros):
    funciones = dict()
    err = None
    try:
        code = ""
        for k, v in filtros.iteritems():
            code += "def f%s(campo):\n" % k
            for c in v.split("\n"):
                code += "\t%s\n" % c

            code += "\treturn campo\n"
            code += "\n"

        modulo = imp.new_module('modulo')
        exec code in modulo.__dict__

        for k in filtros.iterkeys():
            funciones[k] = modulo.__dict__["f" + k]
    except Exception as e:
        err = error(e, 2)

    return funciones, err


# campos definidos
def crea_modulo(valores, data):
    funciones = dict()
    err = None
    try:
        if data["campos"]:
            code = ""
            for nombre_valor in valores:
                code += "def f%s(valores):\n" % nombre_valor[0]
                for i, campo in enumerate(data["campos"]):
                    code += "\t%s=valores[%d]\n" % (campo, i)

                code += "\n"
                for v in nombre_valor[1].split("\n"):
                    code += "\t%s\n" % v

                code += "\treturn %s\n" % nombre_valor[0]
                code += "\n"

            modulo = imp.new_module('modulo')
            exec code in modulo.__dict__

            for nombre_valor in valores:
                funciones[nombre_valor[0]] = modulo.__dict__["f" + nombre_valor[0]]
    except Exception as e:
        err = error(e, 2)

    return funciones, err


# campos por registro
def exec_codigo(nombre, code, db):
    global _global
    modulo = imp.new_module('modulo')
    setattr(modulo, "_db", db)
    setattr(modulo, "_global", _global)

    try:
        exec code in modulo.__dict__

        resul = modulo.__dict__[nombre]
        _global = modulo.__dict__["_global"]
        return resul, None
    except Exception as e:
        return None, error(e, 0)


# condiciones tabla
def exec_funcion(code, db):
    global _global
    modulo = imp.new_module('modulo')
    setattr(modulo, "_db", db)
    setattr(modulo, "_global", _global)

    try:
        funcion = "def f():\n"
        funcion += " global _global\n"
        for linea in code.split("\n"):
            funcion += " %s\n" % linea

        exec funcion in modulo.__dict__

        fun = modulo.__dict__["f"]
        resul = fun()
        _global = modulo.__dict__["_global"]
        return resul, None

    except Exception as e:
        return None, error(e, 2)


# código inicial/final
def codigo(code, data, db):
    global _global
    modulo = imp.new_module('modulo')
    setattr(modulo, "_pgi", data)
    setattr(modulo, "_db", db)
    setattr(modulo, "_global", _global)

    try:
        exec code in modulo.__dict__
        resul = modulo.__dict__["_pgi"]
        _global = modulo.__dict__["_global"]
        return resul, None

    except Exception as e:
        return data, error(e, 0)
