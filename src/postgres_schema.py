
LIST_DATABASES = """
    SELECT
        datname
    FROM
        pg_database
    WHERE
        NOT datistemplate
        AND datname <> 'postgres'
"""

LIST_TABLAS = """
    SELECT
        table_name
    FROM
        information_schema.tables
    WHERE
        table_schema = 'public'
"""

LIST_TABLAS_AND_PRIMARY_KEY = """
    SELECT
        n.nspname AS "Schema",
        c.relname AS "Table Name",
        c.relhaspkey AS "Has PK"
    FROM
        pg_catalog.pg_class c
    JOIN
        pg_namespace n
    ON (c.relnamespace = n.oid
        AND n.nspname NOT IN ('information_schema', 'pg_catalog')
        AND c.relkind='r')
    WHERE n.nspname = 'public'
    ORDER BY c.relname
"""

LIST_TABLAS_WITHOUT_PRIMARY_KEY = """
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

LIST_CAMPOS = """
    SELECT
        column_name,
        data_type,
        character_maximum_length
    FROM
        information_schema.columns
    WHERE
        table_name ='%s'
"""

# otra forma
LIST_CAMPOS1 = """
    SELECT attrelid::regclass, attnum, attname
    FROM pg_attribute
    WHERE attrelid = '%s'::regclass
    AND attnum > 0
    AND NOT attisdropped
    ORDER BY attnum
"""

#esta es muy lenta
LIST_PRIMARY_KEY1 = """
    SELECT
        c.column_name,
        c.data_type
    FROM
        information_schema.table_constraints tc
    JOIN
        information_schema.constraint_column_usage AS ccu USING (constraint_schema, constraint_name)
    JOIN
        information_schema.columns AS c ON c.table_schema = tc.constraint_schema
        AND tc.table_name = c.table_name
        AND ccu.column_name = c.column_name where constraint_type = 'PRIMARY KEY'
        AND tc.table_name = '%s'
"""

# y esta
LIST_PRIMARY_KEY2 = """
    SELECT
      pg_attribute.attname,
      format_type(pg_attribute.atttypid, pg_attribute.atttypmod)
    FROM pg_index, pg_class, pg_attribute, pg_namespace
    WHERE
      pg_class.oid = '%s'::regclass AND
      indrelid = pg_class.oid AND
      nspname = 'public' AND
      pg_class.relnamespace = pg_namespace.oid AND
      pg_attribute.attrelid = pg_class.oid AND
      pg_attribute.attnum = any(pg_index.indkey)
     AND indisprimary
"""

#  https://wiki.postgresql.org/wiki/Retrieve_primary_key_columns
LIST_PRIMARY_KEY = """
    SELECT a.attname, format_type(a.atttypid, a.atttypmod) AS data_type
    FROM   pg_index i
    JOIN   pg_attribute a ON a.attrelid = i.indrelid
           AND a.attnum = ANY(i.indkey)
    WHERE  i.indrelid = '%s'::regclass
    AND    i.indisprimary;
"""

LIST_INDEXES = """
    SELECT
        i.relname as index_name,
        a.attname as column_name
    FROM
        pg_class t,
        pg_class i,
        pg_index ix,
        pg_attribute a
    WHERE
        t.oid = ix.indrelid
        AND i.oid = ix.indexrelid
        AND a.attrelid = t.oid
        AND a.attnum = ANY(ix.indkey)
        AND t.relkind = 'r'
        AND t.relname = '%s'
"""

LIST_CONSTRAINT = """
    SELECT
        tc.constraint_name, kcu.column_name,
        ccu.table_name AS foreign_table_name,
        ccu.column_name AS foreign_column_name
    FROM
        information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
        ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage AS ccu
        ON ccu.constraint_name = tc.constraint_name
    WHERE
        constraint_type = 'FOREIGN KEY' AND tc.table_name='%s'
    ORDER BY
        ccu.table_name, kcu.column_name
"""

# solo optiene el nombre y el tipo
LIST_CONSTRAINT1 = """
    SELECT
        constraint_name, constraint_type
    FROM
        information_schema.table_constraints
    WHERE
        table_name = '%s'
"""

SHOW_ENCODE = """
    SELECT
        pg_encoding_to_char(encoding)
    FROM
        pg_database
    WHERE datname = '%s'
"""

COUNT_TABLES1 = """
    SELECT
      relname,reltuples
    FROM pg_class C
    LEFT JOIN pg_namespace N ON (N.oid = C.relnamespace)
    WHERE
      nspname NOT IN ('pg_catalog', 'information_schema') AND
      relkind='r' AND nspname= 'public'
"""

COUNT_TABLES = """
    SELECT relname, reltuples
    FROM pg_class r JOIN pg_namespace n ON (relnamespace = n.oid)
    WHERE relkind = 'r' AND n.nspname = 'public'
    ORDER BY relname
"""