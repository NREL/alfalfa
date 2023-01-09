import sys
import os
SCRIPT_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../../../../../../eptobrick'))
print(SCRIPT_DIR)
sys.path.append(os.path.dirname(SCRIPT_DIR))
from extractor import epparser as Parser


def main(argv):

    parser = Parser()
    opm = parser.load(argv[0])
    test = parser.walkElements(opm)
    parser.connectComponents()
    parser.cleanupPredicates()
    for subj in parser.components.values():
        if subj.btype != "":
            print(f"{subj.name}, a {subj.btype}")
            for predicate in subj.bpredicates.keys():
                for obj in subj.bpredicates[predicate]:
                    try:
                        print(f"\t {predicate} {obj.name}, a {obj.btype}")
                    except:
                        print(f"\t {predicate} {obj} !!STRING!!")
    parser.createGraph()
    parser.saveGraph()
    return True

if __name__ == "__main__":
   main(sys.argv[1:])