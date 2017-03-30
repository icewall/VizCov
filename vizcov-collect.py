import sys
import os
import shutil
import argparse
import lib.utils as utils
from lib.utils import DrRunController

class VizCovCollector(object):
    def parse_args(self):
        parser = argparse.ArgumentParser(description='VizCov by Icewall')
        parser.add_argument("-i",dest="corpus_dir",help="Path to corpus directory")
        parser.add_argument("-o",dest="out_dir",help="Path to store coverage data")
        parser.add_argument("-f",dest="input_file",help="File to be read instead of typical stdin arg")
        parser.add_argument("-t",dest="time_out",type=int,default=99999999,help="Timeout in ms")
        parser.add_argument("-c",dest="config_path",default="",help="Path to config file")
        parser.add_argument("argv",nargs='+')
        args = parser.parse_args()
        return args

    def collect(self,corpus_dir,out_dir,in_file,time_out,config_path,app_path,args):
        #check operating system and turn off crash handling
        utils.turn_off_crash_handling()
        args = " ".join(args)
        import time
        start = time.time()
        for dir_path,dir_name,files in os.walk(corpus_dir):
            for f in files:
                file_path = os.path.join(dir_path,f)
                if in_file:
                    shutil.copy(file_path,in_file)
                    _args = args
                else:
                    _args = args.replace("@@",file_path)
                DrRunController.run(out_dir,file_path,time_out,config_path,app_path,_args)                       
        print "It took : {0}".format(time.time() - start)
              
if __name__ == "__main__":
    collector = VizCovCollector()
    args = collector.parse_args()
    collector.collect( args.corpus_dir,
                       args.out_dir,
                       args.input_file,
                       args.time_out,
                       args.config_path,
                       args.argv[0],
                       args.argv[1:]
                      )