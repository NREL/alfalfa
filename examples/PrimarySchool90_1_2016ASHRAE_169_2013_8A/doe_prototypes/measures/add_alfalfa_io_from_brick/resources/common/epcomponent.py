from itertools import combinations
try:
    import opyplus as op
except:
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", 'opyplus'])
    import opyplus as op
from utils import getEPType, mergeDicts, Nuncius
import os, json

m = Nuncius(debug = 1)

class Extractor():

    def __init__(self, verbose=3) -> None:
        m.debug = verbose

        self.components = {}

        with open(os.path.join(os.path.dirname(__file__), 'commonMap.json')) as f:
            self.epbindings = json.load(f)

    def mergeBindings(self, dictB):
        self.epbindings = mergeDicts(self.epbindings, dictB)

    def load(self, eppath):
        '''
        Load an IDF file.

        Args:
        eppath : str
            Path to the IDF
        Returns:
        idf
            The eppy.IDF instance of the EnergyPlus model
        '''
        opidf = op.Epm()
        opm = opidf.load(eppath, check_length=False)
        m.printMessage(f'Loaded file: {eppath}')
        self.outname = eppath.replace('.idf', '')
        return opm

    def walkElements(self, opm):
        for category in opm:
            for element in category:
                newelements = self.getComponent(element, opm.nodelist)
                for newelement in newelements:
                    if newelement.name in self.components.keys():
                        if self.checkduplicate(newelement):
                            m.printMessage(f"Element {newelement.name} already exists. It will be updated.", lvl="debug")
                            newelement.update(self.components[newelement.name])
                        else:
                            m.printMessage(f"Found two elements with identical name: \
                            \n\t {newelement.name}, a {newelement.etype} (new element)\n \
                            and \n \
                            \n\t {self.components[newelement.name].name}, a {self.components[newelement.name].etype} (existing element)\n \
                            The new element will be renamed.", lvl="debug")
                            suff = 0
                            while newelement.name in self.components.keys():
                                if self.checkduplicate(newelement):
                                    newelement.update(self.components[newelement.name])
                                    break
                                else:
                                    suff +=1
                                    newelement.name = newelement.name.split('__')[0] + f"__{suff}"
                    self.components[newelement.name] = newelement
        m.printMessage(f"Found {len(self.components.keys())} elements in the IDF", lvl='debug')
        
    def checkduplicate(self, element):
        suspect = self.components[element.name]
        if suspect.idfelem != None:
            return suspect.idfelem == element.idfelem
        else:
            return suspect.name == suspect.name

    def connectComponents(self):

        count = 0
        for left, right in combinations(list(self.components.values()), 2):
            fedbyinter = [i for i in left.inlets if i in right.outlets]
            feedsinter = [i for i in left.outlets if i in right.inlets]
            if len(feedsinter) > 0:
                self.components[left.name].addPredicate("feeds", [right])
                count += 1
                m.printMessage(f"{left.name} feeds {right.name}", lvl='debug')
            elif len(fedbyinter) > 0:
                self.components[right.name].addPredicate("feeds", [left])
                m.printMessage(f"{right.name} feeds {left.name}", lvl='debug')
                count += 1

        m.printMessage(f"Found {count} connections.", lvl='debug')



    def getComponent(self, element, nodelists):
            res = []
            if isinstance(element, Point):
                return element
            epcomponent = Component(element, nodelists)
            if epcomponent.etype in self.epbindings.keys():
                bindings = self.epbindings[epcomponent.etype]
                epcomponent.assignBasics(bindings)
                res.extend([epcomponent])
                for method in bindings["rules"].keys():
                    m.printMessage(f"Applying method {method} using args {bindings['rules'][method]} for {epcomponent.name}", lvl='debug')
                    if hasattr(epcomponent, str(method)):
                        mth = getattr(epcomponent, str(method))
                        subcomponents = mth(bindings["rules"][method])
                        if isinstance(subcomponents, list):
                            for subc in subcomponents:
                                res.extend(self.getComponent(subc, nodelists))
                    elif hasattr(self, str(method)):
                        mth = getattr(self, str(method))
                        subcomponents = mth(bindings["rules"][method], epcomponent)
                        res.extend(subcomponents)
                    else:
                        m.printMessage(f"Could not find method: {method} for {epcomponent.name}", lvl='debug')
                return res
            else: 
                m.printMessage(f"Category not defined in the EP bindings dict: {epcomponent.etype}", lvl='debug')
                return []

class Point():
    def __init__(self, name, btype, parent) -> None:
        self.name = name
        self.idfelem = None
        self.etype = "Node"

class Component():
    def __init__(self, idfelem, nodelists) -> None:
        self.name = None
        self.epname = None
        self.idfelem = idfelem
        self.etype = getEPType(idfelem)
        self.inlets = []
        self.outlets = []
        self.nodes = []
        self.connectors = []
        self.nodelists = nodelists

    def assignBasics(self):
        # restore bindings as a module-dependent method (e.g., ep2brick)
        if hasattr(self.idfelem, "name"):
            self.name = self.idfelem.name
            self.epname = self.name
        else:
            self.name = self.etype.replace(':', '_') + "_UNNAMED"

    def update(self, other):
        m.printMessage(f"Updating {self.name}. Checking for conflicts.", lvl="debug")
        same = True
        for prop in ["name", "epname", "idfelem", "etype"]:
            if getattr(self, prop) != getattr(other, prop):
                same = False
                break
        if same:
            self.inlets.extend([i for i in other.inlets if i not in self.inlets])
            self.outlets.extend([i for i in other.outlets if i not in self.outlets])
            self.nodes.extend([i for i in other.nodes if i not in self.nodes])
            self.connectors.extend([i for i in other.connectors if i not in self.connectors])
            m.printMessage(f"Successfully updated {self.name}", lvl="success")
        else:
            raise Exception(f"Error while updating {self.name} (an EP {self.etype}) with values from {other.name}: conflicts exist", lvl="failure")


    def addInlets(self, inlets):
        m.printMessage(f"Adding {inlets} to {self.name}, which currently has {len(self.inlets)} inlets.", lvl='debug')
        for inlet in inlets:
            if hasattr(self.idfelem, inlet):
                self.inlets.append(getattr(self.idfelem, inlet))
            else:
                self.inlets.append(inlet)
        m.printMessage(f"{self.name} now has {len(self.inlets)} inlets.", lvl='debug')
    
    def addOutlets(self, outlets):
        m.printMessage(f"Adding {outlets} to {self.name}, which currently has {len(self.outlets)} outlets.", lvl='debug')

        for outlet in outlets:
            if hasattr(self.idfelem, outlet):
                self.outlets.append(getattr(self.idfelem, outlet))
            else:
                self.outlets.append(outlet)
        m.printMessage(f"{self.name} now has {len(self.outlets)} outlets.", lvl='debug')
        

    def addNodes(self, nodes, conn=None):
        for node in nodes:
            if hasattr(self.idfelem, node):
                self.nodes.append(getattr(self.idfelem, node))
            else:
                self.nodes.append(node)

    def addNodelist(self, nodelists):
        for key in nodelists.keys():
            for nodelist in nodelists[key]:
                m.printMessage(f"Fetching NodeList: {getattr(self.idfelem, nodelist)}", lvl='debug')
                found = False
                for nlist in self.nodelists:
                    if getattr(self.idfelem, nodelist) == nlist.name:
                        nodelistref = nlist
                        found = True
                        m.printMessage(f"Found NodeList {nlist.name}", lvl='debug')
                if not found:
                    m.printMessage(f"Could not find IDF declaration for {getattr(self.idfelem, nodelist)}")
                if key == "inlets":
                    self.extensibleMethod([{"method": "addInlets", "type_": "node", "attr_": "name"}], otheridf=nodelistref)
                elif key == "outlets":
                    self.extensibleMethod([{"method": "addOutlets", "type_": "node", "attr_": "name"}], otheridf=nodelistref)

    def addConnectors(self, connectors):
        for connector in connectors:
            if hasattr(self.idfelem, connector):
                self.inlets.append(getattr(self.idfelem, connector))
            else:
                self.inlets.append([connector])
    def unpackList(self, params):
        eplist = params["list"]
        type_ = params["type_"]
        attr_ = params["attr_"]
        res = []

        try:
            listname = eplist.name
        except AttributeError:
            listname = eplist
        m.printMessage(f"Unpacking list {listname}.", lvl='debug')

        # This code works for EP 9.6
        # EP >21.1 seems like it uses TYPE_ATTR_NUMBER instead of TYPE_NUMBER_ATTR (e.g., "node_name_1" instead of "node_1_name")
        for i in range(1, 100):
            if attr_ != "":
                attrstr = f"{type_}_{i}_{attr_}"
            else:
                attrstr = f"{type_}_{i}"
            try:
                m.printMessage(f"Searching for {attrstr}.", lvl='debug')
                if getattr(eplist, attrstr) is not None:
                    res.extend([getattr(eplist, attrstr)])
                
            except:
                try:
                    attrstr = f"{type_}_{attr_}_{i}"
                    m.printMessage(f"Not found. Attempting with {attrstr}.", lvl='debug')
                    if getattr(eplist, attrstr) is not None:
                        res.extend([getattr(eplist, attrstr)])
                    m.printMessage("Success.", lvl='debug')
                except:
                    break
        if len(res) > 0:
            m.printMessage(f"Success. Found {len(res)} components in {listname}", lvl='debug')
        else:
            m.printMessage(f"There are no components in list {listname} with type {type_} and attribute {attr_}.", lvl='debug')
        return res

    def getListElements(self, listname):
        try:
            return [getattr(self.idfelem, element) for element in listname if getattr(self.idfelem, element) is not None]
        except TypeError:
            return listname

    def unpackBranch(self, branchnames):
        subcomponents = []
        for branch in branchnames:
            bsc = self.unpackList({"list" : branch, "type_" : 'component', "attr_": 'name'})
            subcomponents.extend(bsc)
        return subcomponents

    def unpackBranchList(self, branchlistnames):
        branchlists = self.getListElements(branchlistnames)
        subcomponents = []
        for branchlist in branchlists:
            branches = self.unpackList({"list" : branchlist, "type_" : 'branch', "attr_": 'name'})
            self.unpackBranch(branches)
        return subcomponents


    def genericUnpack(self, unpacklist):
        if isinstance(unpacklist[0], str):
            if hasattr(self.idfelem, unpacklist[0]):
                subcomponents = self.getListElements(unpacklist)
            else:
                subcomponents = unpacklist
        else:
            subcomponents = unpacklist
        return subcomponents

    def zoneEquipment(self, equiplist):
        self.zoneequip = self.unpackList({"list" : self.idfelem, "type_" : 'zone_equipment', "attr_": 'name'})


    def extensibleMethod(self, mdict, otheridf=None):
        if otheridf is not None:
            idfelem = otheridf
        else:
            idfelem = self.idfelem
        subcomponents = []
        for meth in mdict:
            if hasattr(self, meth["method"]):
                mth = getattr(self, meth["method"])
                m.printMessage(f"{self.name}: \tUsing method {meth['method']}", lvl='debug')
                unpacked = self.unpackList({"list" : idfelem, "type_" : meth["type_"], "attr_": meth["attr_"]})
                if "predicate" in meth.keys():
                    extendedlist = None
                    self.manualPredicate({"predicate": meth["predicate"], "elements": unpacked})
                else:
                    extendedlist = mth(unpacked)
                if extendedlist is not None:
                    subcomponents.extend(extendedlist)

        return subcomponents
