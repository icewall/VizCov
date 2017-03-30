import sqlite3
import os
import traceback
import sys
import pdb

class VizCovDB(object):       
    
    def __init__(self,dbPath):
        self._dbPath = dbPath
        self._dbHandler = sqlite3.connect(self._dbPath)
        self._dbHandler.row_factory = sqlite3.Row

    def add_corpus_file(self,corpus_file_path,file_size,md5):
        #XXX: add md5 checking to do not insert same file ???
        c = self._dbHandler.cursor()
        c.execute("INSERT INTO corpus VALUES(null,?,?,?)",(corpus_file_path,file_size,md5))
        self._dbHandler.commit()        
        return c.lastrowid        

    def is_module_analyzed(self,module_name):
        rows = self._dbHandler.execute("SELECT * FROM module WHERE name= ? ",(module_name,)).fetchall()
        return len(rows)

    def update_bb(self,bb_rva,bb_size):
        c = self._dbHandler.cursor()
        c.execute("UPDATE bb SET hit=1 WHERE ? <= start_ea AND start_ea < ? ",(bb_rva,bb_rva+bb_size))
        self._dbHandler.commit()
        return

    def get_bbs(self,rva,size):
        return self._dbHandler.execute("SELECT * FROM bb WHERE ? <= start_ea AND start_ea < ? ",(rva,rva+size)).fetchall()

    def add_module(self,module_path,image_base,idb_path):
        name = os.path.basename(module_path)        
        c = self._dbHandler.cursor()
        c.execute("INSERT INTO module VALUES(null,?,?,?,?)",(name,image_base,module_path,idb_path))
        self._dbHandler.commit()        
        return c.lastrowid

    def add_function(self,module_id,name,bbl_amount):
        c = self._dbHandler.cursor()
        c.execute("INSERT INTO function VALUES(null,?,?,?)",(module_id,name,bbl_amount))
        self._dbHandler.commit()
        return c.lastrowid

    def add_basic_block(self,function_id,start_ea,end_ea):
        c = self._dbHandler.cursor()
        c.execute("INSERT INTO bb VALUES(null,?,?,?,0)",(function_id,start_ea,end_ea))
        self._dbHandler.commit()
        return c.lastrowid

    def add_file_coverage(self,corpus_file_id,bb_rva,bb_size):
        bbs = self.get_bbs(bb_rva,bb_size)
        for bb in bbs:
            self._dbHandler.execute("INSERT INTO bb_corpus VALUES(?,?)",(bb["id"],corpus_file_id))
        return self._dbHandler.commit()                                    

    def get_bbs_for_module(self,module_name):        
        sqlQuery = """
                    SELECT * FROM bb as b 
                    JOIN function as f on b.function_id=f.id
                    JOIN module as m on f.module_id=m.id
                    WHERE m.name=?
                   """
        return self._dbHandler.execute(sqlQuery, (module_name,)).fetchall()

    def get_coverage(self,module_name):        
        sqlQuery = """
                    SELECT f.id,f.name,f.bbl_amount,count(*)"covered" FROM bb as b 
                    JOIN function as f on b.function_id=f.id
                    JOIN module as m on f.module_id=m.id						
                    WHERE m.name=? AND b.hit !=0
                    GROUP BY f.id
                   """
        return self._dbHandler.execute(sqlQuery, (module_name,)).fetchall()

    def get_coverage_for_function(self,module_name,function_name):        
        sqlQuery = """
                    SELECT * FROM bb as b 
                    JOIN function as f on b.function_id=f.id
                    JOIN module as m on f.module_id=m.id						
                    WHERE m.name=? AND f.name = ? AND b.hit !=0
                   """
        return self._dbHandler.execute(sqlQuery, (module_name,function_name)).fetchall()

    def get_files_for_address(self,ea):       
        bb = self.get_bb_id(ea)
        if not len(bb):
            return            
             
        sqlQuery = """
                    SELECT c.file_path,c.file_size,c.md5 FROM bb_corpus as bc
                    JOIN corpus as c ON bc.corpus_id = c.id
                    JOIN bb as b     ON bc.bb_id = b.id
                    WHERE b.id = ?
                   """
        #for a huge number of files we would need to return here generator
        bb = bb[0]
        return self._dbHandler.execute(sqlQuery, (int(bb["id"]),)).fetchall()
        
    def get_bb_id(self,ea):
        sqlQuery = """
                   SELECT * FROM bb
                   WHERE ? >= start_ea AND ? < end_ea
                   """
        return self._dbHandler.execute(sqlQuery, (ea,ea)).fetchall()

    def updateFunctions(self,functions):
        pass
    
    def get_db_handler(self):
        return self._dbHandler
    
    def get_db_path(self):
        return self._dbPath
    
    def table_exists(self,table_name):
        rows = self._dbHandler.execute("SELECT name FROM sqlite_master where name = ?",(table_name,)).fetchall()
        return len(rows)

    def create_tables(self,tables):
        for table in tables:
            try:
                self._dbHandler.execute(table)
            except sqlite3.Error as e:
                #Logger.log("An error occurred: "+ e.args[0])
                pass
        self._dbHandler.commit()
    
    def drop_tables(self,tables):
        for table in tables:
            try:
                self._dbHandler.execute("DROP TABLE %s" % table)
            except sqlite3.Error as e:
                #Logger.log("An error occurred:" + e.args[0])
                pass
        self._dbHandler.commit() 
