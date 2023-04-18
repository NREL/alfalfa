
from termcolor import colored
import os, json

def getListComponents(idflist, type, value):
        components = []
        i = 1
        while True:
            try:
                components.append(getattr(idflist, f'{type}_{i}_{value}'))
                i += 1
            except:
                break
        return list(filter(None, components)) #sometimes we end up with trailing 'None' values

def getEPType(inp):
        return inp._table._dev_descriptor.table_name

def mergeDicts(dictA, dictB):
    for obj in dictB.keys():
        if obj in dictA.keys():
            entry = dictB[obj]
            for key in entry.keys():
                if key not in dictA[obj].keys():
                    dictA[obj][key] = entry[key]
                else:
                    print(f"Warning! Could not merge an entry: {key} appears in both dictionaries.")
    return dictA

class Nuncius():

    def __init__(self, debug) -> None:
        self.debug = debug

    def printMessage(self, message, lvl='info'):
            if lvl == 'info':
                print(colored(f'Info:\t{message}', 'blue'))
            elif lvl == 'debug' and self.debug > 2:
                print(colored(f'Debug:\t{message}', 'yellow'))
            elif lvl == 'success':
                print(colored(f'Success:\t{message}', 'green'))
            elif lvl == 'failure':
                print(colored(f'Failed:\t{message}', 'red'))