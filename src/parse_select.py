# -*- coding: utf-8 -*-


def alias(funcion, cadena):
    ini = cadena.upper().find(" AS ")
    if ini >= 0:
        return cadena[ini + len(" AS "):]
    else:
        return funcion.strip()


def saca_campos(lista):
    campos = list()

    for cadena in lista:
        izq = ""
        parentesis = 0
        ok = False
        for i, c in enumerate(cadena):
            if c == "(":
                parentesis += 1
            elif c == ")":
                parentesis -= 1
                if parentesis == 0:
                    ok = True
                    break
            elif parentesis == 0:
                izq += c

        if ok:
            campos.append(alias(izq, cadena[i + 1:]))
        else:
            campos.append(alias(izq, izq))

    return campos


def campos2list(cadena):
    lista = list()
    izq = ""
    parentesis = 0
    ok = False

    for c in cadena:
        if c != "," or parentesis > 0:
            izq += c

        if c == "(":
            parentesis += 1
        elif c == ")":
            parentesis -= 1
            if parentesis == 0:
                ok = True
        elif c == ",":
            if parentesis == 0 or ok:
                lista.append(izq.strip())
                izq = ""

    lista.append(izq.strip())
    return lista


def parse_select(db, sql, campos_ordenados=False):
    """
    Retorna la lista de tablas, lista de campos y la sql (modificada si campos='*') de la select dada ó
    el valor de retorno de un insert
    :param db: base de datos
    :param sql: sentencia sql
    :param campos_ordenados: boolean si True y los campos de la select es '*' retorna estos ordenados
    :return: lista_tablas, lista_campos, sql
    """

    db.error = None
    sql = sql.strip()

    ini = sql.upper().find("RETURNING")
    if sql.upper().find("INSERT") == 0 and ini > 0:
        id = sql[ini + len("RETURNING"):].split()
        return [], id, sql

    ini = sql.find(" ")
    ini2 = sql.find("\t")
    ini3 = sql.find("\n")

    if ini2 >= 0 and  ini > ini2:
        ini = ini2

    if ini3 >= 0 and ini3 < ini:
        ini = ini3

    fin = sql.upper().find("FROM")

    if sql.upper().find("SELECT") != 0 or fin < 0:
        return [], [], sql

    campos = campos2list(sql[ini:fin].strip())
    lis_campos = saca_campos(campos)

    tablas = sql[fin + len("FROM"):]
    tablas = tablas.replace("\n", " ")
    tablas = tablas.replace("\t", " ")
    tablas = tablas.split(",")

    i = 0
    final = False
    lis_tablas = list()
    for t in tablas:
        t = t.strip()
        if t.upper().find("WHERE") > 0\
                or t.upper().find("GROUP") > 0\
                or t.upper().find("HAVING") > 0\
                or t.upper().find("ORDER") > 0\
                or t.upper().find("LIMIT") > 0:
            final = True
        t = t.split(" ")
        lis_tablas.append(t[0])
        if final:
            break

    lis_campos1 = lis_campos
    if len(lis_campos) == 1 and lis_campos[0] == "*" or lis_campos[0] == "":
        lis_campos1 = list()
        lis_campos2 = list()
        for t in lis_tablas:
            cam_tabla = db.get_campos(t)
            if campos_ordenados:
                cam_tabla = sorted(cam_tabla)
            for c in cam_tabla:
                if len(lis_tablas) == 1:
                    lis_campos1.append(c[0])
                    lis_campos2.append('"%s"' % c[0])
                else:
                    lis_campos1.append("%s.%s" % (t, c[0]))
                    lis_campos2.append('"%s.%s"' % (t, c[0]))
        sql = sql[:ini] + " " + ",".join(lis_campos2) + " " + sql[fin:]

    return lis_tablas, lis_campos1, sql

if __name__ == '__main__':
    from dbpostgres import DbPostgres

    db = DbPostgres()
    db.conecta("localhost", 5432, "openerp", "openerp", "prueba")

    sql = "INSERT INTO a1 VALUES (default) RETURNING id"
    sql = "select id from a1 where num=@csv.precio"

    sql = "select CONCAT(id,id2,id3), MIN(id) from a1"

    sql = """SELECT
    res_partner.name AS _name_,
    res_partner.id AS _id_,
    res_partner.country_id
FROM
    res_partner
ORDER BY
    res_partner.name ASC"""


    tablas, campos, sql = parse_select(db, sql)

    print tablas
    print campos
    print sql
