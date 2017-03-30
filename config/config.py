import os

IDA_PATH=r"x:\IDA_6.9"
IDA_PATH_x86 = os.path.join(IDA_PATH,"idaq.exe")
IDA_PATH_x64 = os.path.join(IDA_PATH,"idaq64.exe")
DRIO_PATH=r"x:\DynamoRIO-Windows-7.0.0-RC1"
DRRUN_X86 = os.path.join(DRIO_PATH,"bin32","drrun.exe") 
DRRUN_X64 = os.path.join(DRIO_PATH,"bin64","drrun.exe") 
DRRUN_CLIENT_PATH=r"x:\vizcov\client_bin"
DRRUN_CLIENT_NAME="dr_vizcov.dll"
DRRUN_CLIENT_X86_PATH = os.path.join(DRRUN_CLIENT_PATH,"x86",DRRUN_CLIENT_NAME)
DRRUN_CLIENT_X64_PATH = os.path.join(DRRUN_CLIENT_PATH,"x64",DRRUN_CLIENT_NAME)
