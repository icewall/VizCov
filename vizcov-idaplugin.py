from idc import *
from idaapi import *
from lib.db import VizCovDB

class VizCov(object):
    def __init__(self):
        self.__line_color = 0xF2E8BF
        self.__bb_color   = 0x00FF00 
        self.__painted_functions = set()

    def event_callback(self, event, *args):
        if event == idaapi.hxe_text_ready:
            vu = args[0]
            if vu.cfunc.entry_ea in self.__painted_functions:
                return 0
            self.__painted_functions.add(vu.cfunc.entry_ea)
            func_name = GetFunctionName(vu.cfunc.entry_ea)
            lines = vu.cfunc.get_pseudocode()
            bbls = self.__db.get_coverage_for_function(GetInputFile(),func_name)
            image_base = get_imagebase()
            for line in lines:
                eas = self.__get_line_eas(vu.cfunc,line)
                for ea in eas:
                    for bb in bbls:
                        start_ea = image_base + bb["start_ea"]
                        end_ea   = image_base + bb["end_ea"]
                        if ea >= start_ea and ea < end_ea:
                            line.bgcolor = self.__line_color                                                                    
        return 0

    def install_hexrays_callback(self):
        try:
            idaapi.remove_hexrays_callback(self.event_callback)
        except:
            pass
        idaapi.install_hexrays_callback(self.event_callback)
                
    def coverage(self):        
        self.table = VizCovTable("Coverage Info",modal=False)
        self.table.items = [ [row["name"],str(row["covered"]),str(row["bbl_amount"]),str(row["covered"]*100 / row["bbl_amount"]) ] for row in self.__db.get_coverage(GetInputFile())]        
        self.install_hexrays_callback()
        bbls = self.__db.get_bbs_for_module(GetInputFile())
        image_base = get_imagebase()
        for bb in bbls:
            start_ea = image_base + bb["start_ea"]
            end_ea   = image_base + bb["end_ea"]
            if bb["hit"]:                        
                self.__color_bb(start_ea,end_ea,self.__bb_color)
                print "Time to cover bb 0x{0:X} - 0x{1:X}".format(start_ea,end_ea)
            else:
                print "No coverage for : 0x{0:X}".format(start_ea)
        self.table.show()

    def get_files_for_address(self,ea):
        return self.__db.get_files_for_address(ea - get_imagebase())

    def get_db(self):
        return self.__db

    def show_table(self):
        self.table = VizCovTable("Coverage Info",modal=False)
        self.table.items = [ [row["name"],str(row["covered"]),str(row["bbl_amount"]),str(row["covered"]*100 / row["bbl_amount"]) ] for row in self.__db.get_coverage(GetInputFile())]        
        self.install_hexrays_callback()
        self.table.show()

    def load_db(self,db_path):
        self.__db = VizCovDB(db_path)

    def __color_bb(self,start_ea, end_ea, c):
        ea = start_ea
        while ea < end_ea:
            idaapi.del_item_color(ea)
            idaapi.set_item_color(ea, c)
            ea += idc.ItemSize(ea)

    def __get_line_eas(self,func,line):
        line = line.line
        eas = set()
        for idx in xrange(len(line) - 2):
            
            if line[idx] != idaapi.COLOR_ON or ord(line[idx+1]) != idaapi.COLOR_ADDR:
                continue

            idx += 2
            addr_string = line[idx:idx+idaapi.COLOR_ADDR_SIZE]
            idx += idaapi.COLOR_ADDR_SIZE
            addr = int(addr_string, 16)
            if (addr & idaapi.ANCHOR_MASK) != idaapi.ANCHOR_CITEM:
                continue

            anchor_idx = addr & idaapi.ANCHOR_INDEX
            cit = func.treeitems.at(anchor_idx)
            if cit.ea == 0xFFFFFFFF:
                continue

            eas.add(cit.ea)
        return eas

class VizCovTable(Choose2):
    def __init__(self, title, flags=0, width=None, height=None, embedded=False, modal=False):
        Choose2.__init__(
            self,
            title,
            [ ["Function Name", 30], ["BB covered", 10 | Choose2.CHCOL_DEC ],["BB total", 10 | Choose2.CHCOL_DEC ],["Coverage percent", 10 | Choose2.CHCOL_DEC] ],
            flags = flags,
            width = width,
            height = height,
            embedded = embedded)
        self.n = 0
        self.icon = 5
        self.selcount = 0
        self.modal = modal

    def OnGetLine(self, n):
        return self.items[n]

    def OnSelectLine(self, n):
        self.selcount += 1
        print self.items[n][0]
        print repr(self.items[n][0])
        idc.Jump(idc.LocByName(str(self.items[n][0])) )
    
    def OnGetSize(self):
        return len(self.items)

    def show(self):
        return self.Show(self.modal) >= 0

    def OnRefresh(self, n):
        return n

    def OnClose(self):
            pass

#############################
##      Create plugin object
####################
try:
    print "==================="
    print " VizCov by Icewall "
    print "==================="
    vizcov = VizCov()
    db_path = idaapi.askfile_c(0,"*.sqlite3","Summary coverage db") 
    vizcov.load_db(db_path)
    print "Now you are ready to apply coverage"
    print "vizcov.coverage()                    # run after first run or when ur coverage db got updated"
    print "vizcov.show_table()                  # just to see applied results"
    print "vizcov.get_db()                      # to play with db in raw way"
    print "vizcov.get_files_for_address()       # if u summarize ur corpus with -f flag, u can use this function to get list of corpus files touching specified address"

except:
    print "Exception in user code:"
    print '-'*60
    traceback.print_exc(file=sys.stdout)
    print '-'*60