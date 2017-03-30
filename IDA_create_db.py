import logging
#logging.basicConfig(filename='example1.log',level=logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)
import sqlite3
import os
import sys
import traceback

from idc import *
from idaapi import *
from lib.db import VizCovDB


tblModule =   """
    CREATE TABLE IF NOT EXISTS module(
    id integer primary key,
    name text,
    image_base integer,
    file_path text,
    idb_path  text
    )
    """           
    
tblFunction = """
                CREATE TABLE IF NOT EXISTS function(
                id integer primary key,
                module_id integer,
                name text,
                bbl_amount integer
                )
              """
              
tblBb = """
            CREATE TABLE IF NOT EXISTS bb(
            id integer primary key,
            function_id integer,
            start_ea integer,
            end_ea integer,
            hit integer
            )
        """                      

tblCorpus = """
            CREATE TABLE IF NOT EXISTS corpus(
            id integer primary key,
            file_path text,
            file_size integer,
            md5 text
            )
        """      

#XXX: add foreign keys!!!
tblBbCorpus = """
            CREATE TABLE IF NOT EXISTS bb_corpus(
            bb_id integer,
            corpus_id integer
            )
        """   

tables = [ tblBb,tblFunction,tblModule,tblCorpus,tblBbCorpus]
           
if __name__ == "__main__":
    try:
        idaapi.autoWait()     
        db_path = idc.ARGV[1]    
        db = VizCovDB(db_path)                   
        db.create_tables(tables)
        module_id = db.add_module(GetInputFilePath(),get_imagebase(),GetIdbPath())
        logging.debug("module_id : %d" % module_id)
        for functionEA in Functions():
            function = get_func(functionEA)
            fc = FlowChart(function)
            function_id = db.add_function(module_id,GetFunctionName(functionEA),fc.size)
            logging.debug("Function : %s" % GetFunctionName(functionEA))
            logging.debug("Amount of bbs : %d" % fc.size)
            for bb in fc:
                start_ea = bb.startEA - get_imagebase()
                end_ea   = bb.endEA   - get_imagebase()
                db.add_basic_block(function_id,start_ea,end_ea)
        Exit(0)
    except:
        logging.debug("Exception in user code:")
        logging.debug('-'*60)
        traceback.print_exc(file=sys.stdout)
        logging.debug('-'*60)
    