import os
import sys
import hashlib
import config.config as config
from string import Template
import subprocess
import pefile
import pdb
import logging
#logging.basicConfig(filename='example.log',level=logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)

def is_windows():
    return sys.platform == "win32"

def disable_wer():
    pass

def disable_core_dumps():
    pass

def turn_off_crash_handling():
    if is_windows():
        disable_wer()
    else: 
        #assume for now its linux
        disable_core_dumps()

def get_md5(file_path):
    with file(file_path,'rb') as f:
        data = f.read()
        return hashlib.md5(data).hexdigest()

def is_x86(file_path):
    return get_arch(file_path) == "x86"

def is_x64(file_path):
    return get_arch(file_path) == "x64"

def get_arch(file_path):
    if is_windows():
        pe = pefile.PE(file_path)
        arch = "x86" if pe.OPTIONAL_HEADER.Magic == pefile.OPTIONAL_HEADER_MAGIC_PE else "x64"
        return arch
    else:
        raise Exception("Not implemented yet!!!")

class IDAController(object):
    @staticmethod
    def run(file_path,script_path,script_params):        
        if is_x86(file_path):
            ida_path = config.IDA_PATH_x86
        else:
            ida_path = config.IDA_PATH_x64
        call_str = '%s -A -S"%s %s" \"%s\"' % (ida_path,script_path,script_params,file_path)
        logging.debug(call_str)
        subprocess.call(call_str)

class DrRunController(object):
    @staticmethod
    def run(out_dir,file_path,time_out,config_path,app_path,args):
        config_path_template = ""
        if is_x86(app_path):
            drrun_path =  config.DRRUN_X86
            client_path = config.DRRUN_CLIENT_X86_PATH
        else:
            drrun_path =  config.DRRUN_X64
            client_path = config.DRRUN_CLIENT_X64_PATH        
        if len(config_path):
            config_path_template = "-config_path $config_path"           
        call_template = Template("$drrun -c $client -time_out $time_out -out_dir $out_dir -file_path \"$file_path\" {0} -- \"$app_path\" $args".format(config_path_template)  )
        call_str = call_template.substitute(drrun=drrun_path,client=client_path,time_out=time_out,out_dir=out_dir,file_path=file_path,config_path=config_path,app_path=app_path,args=args)
        print call_str
        return subprocess.call(call_str)