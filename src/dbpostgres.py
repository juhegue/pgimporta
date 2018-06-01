# -*- coding: utf-8 -*-

import datetime
import decimal
import psycopg2
import postgres_schema as SQL


class DbPostgres(object):
    """
    Conexión DB postgres
    """
    def __init__(self):
        self.__conn = None
        self.__auto_commit = True
        self.__error = None
        self.__databases = list()
        self.__database = ""
        self.__rowcount = 0
        self.__column_names = list()
        self.__column_types = list()
        self.__column_ntypes = list()
        self.__column_type_name = dict()

    @staticmethod
    def __str2unicode(txt):
        if type(txt) == str:
            return txt.decode("utf-8")
        return txt

    def conecta(self, host, puerto, usuario, clave, database="postgres"):
        ha_conectado = False
        self.close()
        #print "host:%s, puerto:%s, usuario:%s, clave:%s, database:%s" % (host, puerto, usuario, clave, database)
        try:
            self.__database = database
            self.__conn = psycopg2.connect(database=database, user=usuario, password=clave, host=host, port=puerto)
            cursor = self.__conn.cursor()
            cursor.execute(SQL.LIST_DATABASES)
            self.__conn.commit()
            data = cursor.fetchall()
            cursor.close()

            for d in data:
                self.__databases.append(d[0])

            ha_conectado = True

        except psycopg2.Error as e:
            if self.__conn:
                self.__conn.rollback()
            self.close()
            self.__error = u"DbPostgres: %s " % self.__str2unicode(e.message)

        return ha_conectado

    def close(self):
        if self.__conn:
            self.__conn.close()
            self.__conn = None

        self.__databases = list()
        self.__error = None

    @property
    def esta_conectada(self):
        return True if self.__conn else False

    @property
    def rowcount(self):
        return self.__rowcount

    @property
    def auto_commit(self):
        return self.__auto_commit

    @auto_commit.setter
    def auto_commit(self, si_no):
        self.__auto_commit = si_no

    @property
    def error(self):
        return self.__error

    @error.setter
    def error(self, value):
        self.__error = value

    @property
    def database(self):
        return self.__database

    @property
    def databases(self):
        return self.__databases

    @property
    def column_names(self):
        return self.__column_names

    @property
    def column_types(self):
        return self.__column_types

    @property
    def column_ntypes(self):
        return self.__column_ntypes

    def get_column_type_name(self, ntype):
        if not self.__column_type_name:
            for tipo, nom in self.ejecuta_all("SELECT oid, typname FROM pg_type"):
                self.__column_type_name[tipo] = nom

        if ntype in self.__column_type_name:
            return self.__column_type_name[ntype]

    def actualiza(self, si_no):
        if self.__conn:
            try:
                if si_no:
                    self.__conn.commit()
                else:
                    self.__conn.rollback()
            except Exception, e:
                self.__error = u"DbPostgres: %s " % self.__str2unicode(e.message)
        else:
            self.__error = u"Database no conectada"

    @staticmethod
    def __sql_con_return(sql):
        if sql.strip().upper().find("DROP") == 0:
            return False
        if sql.strip().upper().find("DELETE") == 0:
            return False
        if sql.strip().upper().find("INSERT") == 0 and sql.strip().upper().find("RETURNING") < 0:
            return False
        if sql.strip().upper().find("UPDATE") == 0 and sql.strip().upper().find("RETURNING") < 0:
            return False
        return True

    def __ejecuta(self, sql, tipo):
        if self.__conn:
            self.__error = data = None
            self.__column_names = list()
            self.__column_types = list()
            self.__column_ntypes = list()
            try:
                cursor = self.__conn.cursor()
                cursor.execute(sql)
                self.__rowcount = cursor.rowcount

                if cursor.description:
                    for des in cursor.description:
                        self.__column_names.append(des.name)
                        self.__column_ntypes.append(des.type_code)

                if self.auto_commit:
                    self.__conn.commit()

                if self.__sql_con_return(sql):
                    if tipo == "ONE":
                        tmp = data = cursor.fetchone()

                    elif tipo == "ALL":
                        data = cursor.fetchall()
                        tmp = data[0] if data else None

                    else:   # MANY
                        return cursor

                    if tmp:
                        # TODO:: esto no siempre funciona ya que el valor pude ser None
                        [self.__column_types.append(type(val)) for val in tmp]

                else:
                    data = self.rowcount
                cursor.close()

            except psycopg2.ProgrammingError, e:
                self.restaura()
                self.__error = u"DbPostgres: %s " % self.__str2unicode(e.message)

            except psycopg2.DataError, e:
                self.restaura()
                self.__error = u"DbPostgres: %s " % self.__str2unicode(e.message)

            except psycopg2.IntegrityError, e:
                self.restaura()
                self.__error = u"DbPostgres: %s " % self.__str2unicode(e.message)

            except psycopg2.InternalError, e:
                self.restaura()
                self.__error = u"DbPostgres: %s " % self.__str2unicode(e.message)

            except Exception, e:
                self.restaura()
                self.__error = u"DbPostgres: %s " % self.__str2unicode(e.message)

            return data
        else:
            self.__error = u"Database no conectada"

    def restaura(self):
        if self.auto_commit:
            try:
                self.__conn.rollback()
            except:
                pass

    def ejecuta_one(self, sql):
        return self.__ejecuta(sql, "ONE")

    def ejecuta_all(self, sql):
        return self.__ejecuta(sql, "ALL")

    def ejecuta_many(self, sql):
        return self.__ejecuta(sql, "MANY")

    def ejecuta(self, sql):
        return self.__ejecuta(sql, "ALL")

    @staticmethod
    def resul_iter(cursor, arraysize=1000):
        if type(cursor) is not int:  # DELETE retorna un int
            try:
                while True:
                    results = cursor.fetchmany(arraysize)
                    if not results:
                        break
                    for result in results:
                        yield result
            except psycopg2.ProgrammingError:   # SET datestyle = "ISO, DMY" ó SET datestyle = default;
                                                # no retorna filas y da el error 'no results to fetch'
                pass

    def get_tablas(self):
        """
        Optiene tablas de la BD
        :return: list, tablas de la BD
        """
        tablas = list()
        data = self.ejecuta_all(SQL.LIST_TABLAS)
        if data:
            for d in data:
                tablas.append(d[0])
        return tablas

    def get_tablas_y_primary_key(self):
        """
        Optiene tablas de la BD y si es o no primary key
        :return: list, tablas de la BD y True/False
        """
        tablas = []
        data = self.ejecuta_all(SQL.LIST_TABLAS_AND_PRIMARY_KEY)
        if data:
            for d in data:
                tablas.append([d[1], d[2]])
        return tablas

    def get_tablas_sin_primary_key(self):
        """
        Optiene tablas de la BD sin primary key
        :return: list, tablas de la BD
        """
        tablas = []
        data = self.ejecuta_all(SQL.LIST_TABLAS_WITHOUT_PRIMARY_KEY)
        if data:
            for d in data:
                tablas.append(d[0])
        return tablas

    def get_campos(self, tabla):
        """
        Optiene campos de la tabla
        :param tabla: str, nombre de la tabla
        :return: list, campos de la tabla, cada uno compuesto por la tupla (nombre, tipo dato, longitud dato)
        """
        campos = list()
        data = self.ejecuta_all(SQL.LIST_CAMPOS % tabla)
        if data:
            for c in data:
                campos.append(c)
        else:
            self.__error = u"Tabla '%s' inexistente o sin campos." % tabla
        return campos

    def get_primary_key(self, tabla):
        """
        Optiene campos de la primary key de la tabla
        :param tabla: str, nombre de la tabla
        :return: list, campos de la tabla, cada uno compuesto por la tupla (nombre, tipo dato)
        """
        campos = list()
        data = self.ejecuta_all(SQL.LIST_PRIMARY_KEY % tabla)
        if data:
            for c in data:
                campos.append(c)
        return campos

    def get_encode(self):
        """
        Optiene campos de la primary key de la tabla
        :param tabla: str, nombre de la tabla
        :return: str, encode
        """
        data = self.ejecuta_all(SQL.SHOW_ENCODE % self.database)
        if data:
            return data[0][0]

    def get_indices(self, tabla):   # NO ES CORRECTO
        """
        Optiene campos de la primary key de la tabla
        :param tabla: str, nombre de la tabla
        :return: list
        """
        indices = list()
        data = self.ejecuta_all(SQL.LIST_INDEXES % tabla)
        if data:
            for i in data:
                indices.append(i)
        return indices

    def get_constraints(self, tabla):
        """
        Optiene el nombre del constraint, la columna, tabla relacionada, campo relacionado
        :param tabla: str, nombre de la tabla
        :return: list, nombre, campo, tabla, campo
        """
        constraints = list()
        for constraint in self.ejecuta_all(SQL.LIST_CONSTRAINT % tabla):
            # create_uid_fkey y write_uid_fkey son comunes a todas la tablas y no son necesarios
            if "create_uid_fkey" in constraint[0] or "write_uid_fkey" in constraint[0]:
                continue
            constraints.append(constraint)
        return constraints

    def get_registros_tablas(self):
        """
        Optiene tabla y el nº de registros 'estimados' de cada una
        :param
        :return: list, nombre, regstros
        """
        tmp = list()
        data = self.ejecuta_all(SQL.COUNT_TABLES)
        if data:
            for i in data:
                tmp.append([i[0], i[1]])
        return tmp


if __name__ == '__main__':
    db = DbPostgres()
    db.conecta("localhost", 5432, "openerp", "openerp", "prueba")
    #db.conecta("localhost", 5432, "openerp", "openerp", "Dickmanns")

    sql = "select * from res_partner limit 1 "
    data = db.ejecuta(sql)
    print db.column_names
    print db.column_ntypes
    print db.column_types

    print db.get_encode()

    sql = "SELECT * FROM product_template WHERE name='primero'"
    d = db.ejecuta(sql)
    print d, db.rowcount, db.error

    sql = "UPDATE a1 SET data='aaa' WHERE id>='1'"
    d = db.ejecuta(sql)
    print d, db.rowcount, db.error

    sql = "CREATE TABLE a1 (id serial PRIMARY KEY, num integer, data1 varchar, data2 varchar, data3 varchar);"
    d = db.ejecuta(sql)
    print d, db.rowcount, db.error

    sql = "INSERT INTO a1 VALUES (default) RETURNING id"
    d = db.ejecuta(sql)
    print d, db.rowcount, db.error

    sql = "DELETE from aaa WHERE id1=1"
    d = db.ejecuta(sql)
    print d, db.rowcount

    sql = "INSERT INTO aaa (id1, id2, nombre, descripcion) VALUES (1, 1, 'juan', 'soy yo')"
    d = db.ejecuta(sql)
    print d, db.rowcount

    sql = "UPDATE aaa SET nombre='juan', descripcion='yo' WHERE id1>='1' "
    d = db.ejecuta(sql)
    print d, db.rowcount

    sql = "SELECT * FROM aaa"
    d = db.ejecuta(sql)
    print d, db.rowcount

    db.close()