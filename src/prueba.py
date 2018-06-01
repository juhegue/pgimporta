# -*- coding: utf-8 -*-

from dbpostgres import DbPostgres

# List primary keys for all tables - Postgresql

sql = """
SELECT
    n.nspname AS "Schema",
    c.relname AS "Table Name",
    c.relhaspkey AS "Has PK"
FROM
    pg_catalog.pg_class c
JOIN
    pg_namespace n
ON (
        c.relnamespace = n.oid
    AND n.nspname NOT IN ('information_schema', 'pg_catalog')
    AND c.relkind='r'
)
WHERE n.nspname = 'public'
ORDER BY c.relname
;
"""

sql1 = """
SELECT table_name
    FROM information_schema.tables
    WHERE (table_catalog, table_schema, table_name) NOT IN
          (SELECT table_catalog, table_schema, table_name
               FROM information_schema.table_constraints
               WHERE constraint_type = 'PRIMARY KEY')
      AND table_schema NOT IN ('information_schema', 'pg_catalog')
      AND table_schema='public'
      ORDER BY table_name
    """

sql = """
SELECT
  relname,reltuples
FROM pg_class C
LEFT JOIN pg_namespace N ON (N.oid = C.relnamespace)
WHERE
  nspname NOT IN ('pg_catalog', 'information_schema') AND
  relkind='r' AND nspname= 'public'
"""

sql="""
    SELECT relname, reltuples
    FROM pg_class r JOIN pg_namespace n ON (relnamespace = n.oid)
    WHERE relkind = 'r' AND n.nspname = 'public'
    ORDER BY relname

"""

if __name__ == '__main__':
    db = DbPostgres()

    #if not db.conecta("10.44.1.99", "5432", "odoo", ""):
    if not db.conecta("localhost", "5432", "openerp", ""):
        print db.error
    else:
        print "conectado"
        print db.databases
        #if not db.conecta("10.44.1.99", "5432", "odoo", "", db.databases[0]):
        if not db.conecta("localhost", "5432", "openerp", "", db.databases[0]):
            print db.error
        else:
            print "conectado", db.databases[0]

            #for t in db.get_tablas():
            #    sql = "select count"

            #    print t

            data = db.ejecuta_all(sql)
            if data:
                 for c in data:
                     print c

        db.close()


