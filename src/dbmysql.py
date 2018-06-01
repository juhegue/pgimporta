# -*- coding: utf-8 -*-

import MySQLdb

class DbMySql(object):
    """
    Conexión DB Mysql
    """
    def __init__(self):
        self.__conn = None
        self.__error = None
        self.__databases = []
        self.__database = ""

    def conecta(self, host, puerto, usuario, clave, database=None):
        ha_conectado = False
        self.close()
        try:
            self.__database = database
            if database:
                self.__conn = MySQLdb.connect(host=host, port=puerto, user=usuario, passwd=clave, db=database)
            else:
                self.__conn = MySQLdb.connect(host=host, port=puerto, user=usuario, passwd=clave)
            cursor = self.__conn.cursor()
            cursor.execute("SHOW DATABASES")
            self.__conn.commit()
            data = cursor.fetchall()
            cursor.close()

            for d in data:
                if d[0] != "mysql" and d[0].find("_schema") < 0:
                    self.__databases.append(d[0])

            ha_conectado = True

        except MySQLdb.Error as e:
            self.close()
            self.__error = u"MySQLdb: %s " % str(e)

        return ha_conectado

    def close(self):
        if self.__conn:
            self.__conn.close()
            self.__conn = None

        self.__databases = []
        self.__error = None

    @property
    def error(self):
        return self.__error

    @property
    def database(self):
        return self.__database

    @property
    def databases(self):
        return self.__databases

    def ejecuta(self, sql):
        cursor = self.__conn.cursor()
        try:
            cursor.execute("SHOW TABLES")
            self.__conn.commit()
            return cursor.fetchall()

        except MySQLdb.Error as e:
            self.__error = u"MySQLdb: %s " % str(e)

        finally:
            cursor.close()

if __name__ == '__main__':
    db = DbMySql()
    db.conecta("centos", 3306, "userb2j", "passb2j", "_u_tutorial_juan_fich_NULL")
    if db.error:
        print db.error

    print db.databases
    print db.ejecuta("SHOW TABLES")