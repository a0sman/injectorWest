import sqlite3 as sl
import sys
sys.path.append('..')
import logger
from argparse import ArgumentParser

DB_FILE = 'lcls2_interface.db'
LOGGER = logger.custom_logger(__name__)

def with_con(f):
    """sqlite connection decorator"""
    def with_con_(*args, **kwargs):
        con = sl.connect(DB_FILE)
        try:
            response = f(con, *args, **kwargs)
            con.commit()  # Not always necessary, doesn't hurt for now 
        except sl.Error as e:
            con.rollback()
            LOGGER.info('Unable to perform operation: {0}'.format(e))
            con.close()
            return
        finally:
            con.close()
        return response
    return with_con_

@with_con
def create_table(con, table, fields):
    """Create table with fields
    Example: >>> db_api.create_table('test1', '(hi text, bye integer)')
    """
    cur = con.cursor()
    cur.execute('CREATE TABLE {0} {1}'.format(table, fields))

@with_con
def insert_record(con, table, data):
    """Insert a record for a given table
    Example: >>> db_api.insert_data('test1', '("junk", "stuff")')
    """
    cur = con.cursor()
    cur.execute('INSERT INTO {0} VALUES {1}'.format(table, data))

@with_con
def read_tables(con):
    """Read a list of all tables
    Example: >>> db_api.read_tables()
    [(u'test1',)]
    """
    cur = con.cursor()
    cur.execute('SELECT name from sqlite_master where type="table"')
    return cur.fetchall()

@with_con
def read_table(con, table):
    """Read the current records for a given table
    Example: >>> db_api.read_table('test1')
    [(u'junk', u'stuff')]
    """
    cur = con.cursor()
    cur.execute('SELECT * FROM {0}'.format(table))
    return cur.fetchall()

@with_con
def delete_table(con, table):
    """Delete a table
    Example: db_api.delete_table('test1')
    """
    cur = con.cursor()
    cur.execute('DROP TABLE {0}'.format(table))
