import logging
#logging.basicConfig(filename='example.log',level=logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)
import os
import sys
import pdb
import json
import argparse
import subprocess
import config.config as config
import lib.utils     as utils
from lib.utils  import IDAController
from lib.db     import VizCovDB
from lib.parser import JsonCoverageParser

class VizCovSummary(object):
    def __init__(self):        
        self.__current_working_dir = os.path.dirname(os.path.realpath(__file__))
    
    def parse_args(self):
        parser = argparse.ArgumentParser(description='VizCov by Icewall')
        parser.add_argument("-m",dest="module_path",help="Module path you want to summarize coverage", required=True)
        parser.add_argument("-i",dest="input_dir",help="Coverage dir",required=True)
        parser.add_argument("-o",dest="out_dir",help="Output dir to store database",required=True)
        parser.add_argument("-f",dest="file_cov",action='store_true',help="Activate storing coverage info of each file separetly.Then you can use vizcov.get_files_for_address")
        args = parser.parse_args()
        return args
                                              
    def __get_analyzer_script_path(self):
        return os.path.join(self.__current_working_dir,"IDA_create_db.py")

    def __analyze_module(self,module_path,db_path):
        module_name = os.path.basename(module_path)
        if not os.path.isfile(db_path):
            logging.debug("Module has not been analyzed.")
            logging.debug("Launch IDA Pro")
            IDAController.run(module_path,self.__get_analyzer_script_path(),db_path)
            logging.debug("Database created")
        else:
            logging.debug("Module already analyzed")

    def summary_coverage(self,input_dir,out_dir,module_path,file_cov):
        logging.debug("Summarizing collected coverage")
        coverage_summary = {}
        module_name = os.path.basename(module_path)
        db_path = os.path.join(out_dir,"{0}.sqlite3".format(module_name))
        self.__analyze_module(module_path,db_path)
        db = VizCovDB(db_path)           
        for dir_path,dir_name,files in os.walk(input_dir):
            for f in files:
                coverage_file_path = os.path.join(dir_path,f)
                coverageParser = JsonCoverageParser(coverage_file_path)
                module_coverage  = coverageParser.get_module_coverage(module_name)
                if module_coverage == None: 
                    continue # there is no interesting coverage for us in this file
                corpus_file_path = coverageParser.get_corpus_file_path()
                logging.debug("Adding coverage for : %s" % corpus_file_path)
                if file_cov:
                    md5 = utils.get_md5(corpus_file_path)
                    file_size = os.path.getsize(corpus_file_path)
                    corpus_file_id = db.add_corpus_file(corpus_file_path,file_size,md5)
                for bb in module_coverage["bbls"]:
                    if file_cov:
                        db.add_file_coverage(corpus_file_id,bb["bb_rva"],bb["bb_size"])
                    coverage_summary[ bb["bb_rva"] ] =  bb["bb_size"]

        for bb_rva, bb_size in coverage_summary.items():
            #summarize coverage
            db.update_bb(bb_rva,bb_size)

        logging.debug("Database is ready to load : %s" % db_path)


if __name__ == "__main__":
    vizcovsum = VizCovSummary()
    args = vizcovsum.parse_args()
    vizcovsum.summary_coverage(args.input_dir,
                               args.out_dir,
                               args.module_path,
                               args.file_cov)
            