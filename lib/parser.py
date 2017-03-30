import json
class JsonCoverageParser(object):
    def __init__(self,filePath):
        data = file(filePath,'r').read()
        self.__coverage = json.loads(data)
    
    def get_module_coverage(self,module_name):
        for module_path in self.__coverage["coverage"].keys():
            if module_path.find(module_name) > -1:
                return self.__coverage["coverage"][module_path]
        return None

    def get_corpus_file_path(self):
            return self.__coverage["corpus_file_path"]
    
    def get_modules(self):
        return self.__coverage["coverage"].keys()
