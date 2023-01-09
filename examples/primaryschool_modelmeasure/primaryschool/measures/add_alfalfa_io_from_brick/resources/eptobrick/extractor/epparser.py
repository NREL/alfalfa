import platform, os, json
#import attrs
import opyplus as op
from itertools import combinations
import brickschema
from brickschema.namespaces import BRICK
from rdflib import Namespace, RDFS, RDF, URIRef, Graph
from utils import utils as ut

m = ut.Nuncius(debug = 1)

class Extractor():

    def __init__(self, verbose=3) -> None:
        m.debug = verbose
        self.graph = Graph()
        self.BRICK = Namespace('https://brickschema.org/schema/Brick#') #1.0.1 is not supported anymore
        self.BF = Namespace('https://brickschema.org/schema/Brick#') #BrickFrame -> BRICK
        self.EX = Namespace('http://eptobrick.com#')
        self.graph.bind('brick', self.BRICK)
        #self.graph.bind('brick', self.BF)
        self.graph.bind('rdfs', RDFS)
        self.graph.bind('rdf', RDF)
        self.graph.bind('ep2b', self.EX)

        self.components = {}

        with open(os.path.join(os.path.dirname(__file__), 'dictmap_.json')) as f:
            self.epbindings = json.load(f)

    def load(self, eppath):
        '''
        Load an IDF file.

        Args:
        eppath : str
            Path to the IDF
        Returns:
        idf
            The opyplus.IDF instance of the EnergyPlus model
        '''
        opidf = op.Epm(check_length=False)
        opm = opidf.load(eppath, check_length=False)
        m.printMessage(f'Loaded file: {eppath}')
        self.outname = eppath.replace('.idf', '')
        return opm


    def walkElements(self, opm):
        for category in opm:
            for element in category:
                newelements = self.getComponent(element)
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
                                    m.printMessage(f"While looking for renamed elements, it turns out we already saw {newelement.name} before... Updating it now.")
                                    newelement.update(self.components[newelement.name])
                                    break
                                else:
                                    suff +=1
                                    newelement.name = newelement.name.split('__')[0] + f"__{suff}"
                    self.components[newelement.name] = newelement
        print(f"Found {len(self.components.keys())} elements in the IDF")
        
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
                print(f"{left.name} feeds {right.name}")
            elif len(fedbyinter) > 0:
                self.components[right.name].addPredicate("feeds", [left])
                print(f"{right.name} feeds {left.name}")
                count += 1

        print (f"Found {count} connections.")

    def cleanupPredicates(self):
        for component in self.components.values():
            print(f"{component.name}, a {component.btype}")
            if not isinstance(component, Point):
                for predicate in component.bpredicates.keys():
                    for obj in component.bpredicates[predicate]:
                        if hasattr(obj, "name"):
                            if not isinstance(obj, Component):
                                
                                m.printMessage(f"Converting {obj.name} to a eptobrick component.")
                                for cobj in self.components.values():
                                    if (cobj.idfelem == obj):
                                        component.bpredicates[predicate] = [i for i in component.bpredicates[predicate] if i != obj]
                                        obj = cobj
                                        component.bpredicates[predicate].append(obj)
                                        break
                                    if cobj == list(self.components.values())[-1]:
                                        m.printMessage(f"Warning! Could not find component matching {obj.name} or type {ut.getEPType(obj)}", lvl='error')
                            print(f"\t{predicate} {obj.name}, a {self.components[obj.name].btype}")
                        else:
                            m.printMessage(f"Warning! In {component.name} {predicate} {obj}: could not find {obj}")
        for component in self.components.values():
            if not isinstance(component, Point):
                self.components[component.name] = self.fixPredicates(component)

    def fixPredicates(self, comp):
        
        nextinline = []
        cont = False
        print(f"Fixing {comp.name}")
        while not cont:
            cont = True
            for predicate in comp.bpredicates.keys():
                for obj in comp.bpredicates[predicate]:
                    if not hasattr(obj, "btype"):
                        obj = self.components[obj]
                    if obj.btype == "" and obj.bpredicates != {}:
                        print(f"Found empty object: {obj.name}")
                        nextinline.extend([obj])
                        cont = False
            for nobj in nextinline:
                for predicate in nobj.bpredicates.keys():
                    if predicate in comp.bpredicates.keys():
                        comp.bpredicates[predicate].extend(nobj.bpredicates[predicate])
                    else:
                        comp.bpredicates[predicate] = nobj.bpredicates[predicate]
                for predicate in comp.bpredicates.keys():
                    comp.bpredicates[predicate] = [i for i in comp.bpredicates[predicate] if i != nobj]
            nextinline = []
        return comp
        


    def findNextInLine(self, obj, predicate):
        nextinline = []
        if self.components[obj].btype == "":
            if predicate in self.components[obj].bpredicates.keys():
                for nextobj in self.components[obj].bpredicates[predicate]:
                    nextinline.extend(self.findNextInLine(nextobj, predicate))
                self.components[obj].bpredicates.pop(predicate)
            else:
              nextinline = None
        else:
            nextinline = None
        return nextinline




    def getComponent(self, element):
        res = []
        epcomponent = Component(element)
        if epcomponent.etype in self.epbindings.keys():
            bindings = self.epbindings[epcomponent.etype]
            epcomponent.assignBasics(bindings)
            res.extend([epcomponent])
            for method in bindings["rules"].keys():
                if hasattr(epcomponent, str(method)):
                    mth = getattr(epcomponent, str(method))
                    subcomponents = mth(bindings["rules"][method])
                    if isinstance(subcomponents, list):
                        for subc in subcomponents:
                            res.extend(self.getComponent(subc))
                elif hasattr(self, str(method)):
                    mth = getattr(self, str(method))
                    subcomponents = mth(bindings["rules"][method], epcomponent)
                    res.extend(subcomponents)
                else:
                    m.printMessage(f"Could not find method: {method}", lvl='debug')
            return res
        else: 
            m.printMessage(f"Category not defined in the EP bindings dict: {epcomponent.etype}", lvl='debug')
            return []

    def addSetpoints(self, setpoints, parent):
        components = []
        parentidf = parent.idfelem
        for setpoint in setpoints:
            nodename = getattr(parent.idfelem, setpoint["node"]) + '_Setpoint'
            if setpoint["quantity"] == "Temperature":
                btype = "Temperature_Setpoint"
            else:
                btype = ""

            if parentidf.name in self.components.keys():
                components.extend([Point(nodename, btype, self.components[parentidf.name])])
            else:
                components.extend([Point(nodename, btype, Component(parentidf))])
        return components

    def addSensors(self, setpoints, parent):
        components = []
        parentidf = parent.idfelem
        for setpoint in setpoints:
            nodename = getattr(parent.idfelem, setpoint["node"]) + '_Sensor'
            if setpoint["quantity"] == "Temperature":
                btype = "Temperature_Sensor"
            else:
                btype = ""

            if parentidf.name in self.components.keys():
                components.extend([Point(nodename, btype, self.components[parentidf.name])])
            else:
                components.extend([Point(nodename, btype, Component(parentidf))])
        return components


    def createGraph(self):
        for subj in self.components.values():
            if subj.btype != "":
                self.graph.add((self.EX[self.legalizeURI(subj.name)], RDF['type'], self.BRICK[subj.btype]))
                for predicate in subj.bpredicates.keys():
                    for obj in subj.bpredicates[predicate]:
                        self.graph.add((self.EX[self.legalizeURI(subj.name)], self.BF[predicate], self.EX[self.legalizeURI(obj.name)]))

    def legalizeURI(self, uri):
        return uri.replace(':', '&58').replace(' ', '&20')

    def saveGraph(self):
        self.graph.serialize(destination=f'{self.outname}.ttl', format='turtle')
        return self.graph

class Point():
    def __init__(self, name, btype, parent) -> None:
        self.name = name
        self.btype = btype
        self.bpredicates = {"isPointOf": [parent]}
        self.idfelem = None
        self.etype = "Node"
        self.inlets = []
        self.outlets = []
    def update(self, newelement):
        return None

class Component():
    def __init__(self, idfelem) -> None:
        self.name = None
        self.epname = None
        self.idfelem = idfelem
        self.etype = ut.getEPType(idfelem)
        self.btype = None
        self.inlets = []
        self.outlets = []
        self.nodes = []
        self.connectors = []
        self.bpredicates = {}

    def assignBasics(self, bindings):
        self.btype = bindings["BrickType"]
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
            for pred in other.bpredicates.keys():
                if pred not in self.bpredicates.keys():
                    self.bpredicates[pred] = other.bpredicates[pred]
                else:
                    self.bpredicates[pred].extend([i for i in other.bpredicates[pred] if i not in self.bpredicates[pred]])
            m.printMessage(f"Successfully updated {self.name}", lvl="success")
        else:
            raise Exception(f"Error while updating {self.name} (an EP {self.etype}) with values from {other.name}: conflicts exist", lvl="failure")


    def addInlets(self, inlets):
        #TODO: check for NodeList
        for inlet in inlets:
            if hasattr(self.idfelem, inlet):
                self.inlets.append(getattr(self.idfelem, inlet))
            else:
                self.inlets.append(inlet)
    
    def addOutlets(self, outlets):
        #TODO: check for NodeList
        for outlet in outlets:
            if hasattr(self.idfelem, outlet):
                self.outlets.append(getattr(self.idfelem, outlet))
            else:
                self.outlets.append(outlet)

    def addNodes(self, nodes):
        for node in nodes:
            if hasattr(self.idfelem, node):
                self.inlets.append(getattr(self.idfelem, node))
            else:
                self.inlets.append([node])
    def addNodelist(self, nodelists):
        if "inlet" in nodelists.keys():
            for nodelist in nodelists["inlet"]:
                # m.printMessage(f"Scanning node or nodelist: {nodelist}")
                # if ut.getEPType(getattr(self.idfelem, nodelist)) != "NodeList":
                #     self.addInlets([nodelist])
                #     m.printMessage("It's a node!")
                # else:
                #     m.print("It's a nodelist!")
                self.manualPredicate({"predicate": "isFedBy", "elements": [nodelist]})
                return getattr(self.idfelem, nodelist)

                ## TODO: this returns a string, not an idf element. Why?

        if "outlet" in nodelists.keys():
            for nodelist in nodelists["outlet"]:
                # if isinstance(getattr(self.idfelem, nodelist), str):
                #     self.addOutlets([nodelist])
                # else:
                self.manualPredicate({"predicate": "feeds", "elements": [nodelist]})
                return getattr(self.idfelem, nodelist)

    def addConnectors(self, connectors):
        for connector in connectors:
            if hasattr(self.idfelem, connector):
                self.inlets.append(getattr(self.idfelem, connector))
            else:
                self.inlets.append([connector])

    def addPredicate(self, predicate, elements):
        for element in elements:
            try:
                # we need this try/except, because somehow the hasattr() method returns always False
                ## getattr(element, "name")
                if predicate in self.bpredicates.keys():
                    self.bpredicates[predicate].extend([element for element in elements if element not in self.bpredicates[predicate]])
                    ## self.bpredicates[predicate].extend([element.name for element in elements if element.name not in self.bpredicates[predicate]])
                else:
                    self.bpredicates[predicate] = [element for element in elements]
                    ## self.bpredicates[predicate] = [element.name for element in elements]
            except:
                pass

    def unpackList(self, params):
        eplist = params["list"]
        type_ = params["type_"]
        attr_ = params["attr_"]
        res = []
        
        for i in range(1, 100):
            if attr_ != "":
                attrstr = f"{type_}_{i}_{attr_}"
            else:
                attrstr = f"{type_}_{i}"
            try:
                if getattr(eplist, attrstr) is not None:
                    res.extend([getattr(eplist, attrstr)])
            except:
                break
        #self.addPredicate("hasPart", res)
        return res

    def getListElements(self, listname):
        try:
            return [getattr(self.idfelem, element) for element in listname if getattr(self.idfelem, element) is not None]
        except TypeError:
            return listname

    def unpackBranch(self, branchlistnames):
        branchlists = self.getListElements(branchlistnames)
        subcomponents = []
        for branchlist in branchlists:
            branches = self.unpackList({"list" : branchlist, "type_" : 'branch', "attr_": 'name'})
            for branch in branches:
                bsc = self.unpackList({"list" : branch, "type_" : 'component', "attr_": 'name'})
                subcomponents.extend(bsc)
            self.addPredicate("hasPart", subcomponents)
        return subcomponents

    # def unpackOAS(self, oaslistsnames):
    #     oaslists = self.getListElements(oaslistsnames)
    #     subcomponents = []
    #     for oaslist in oaslists:
    #         #TODO add predicate?
    #         subcomponents.extend(self.unpackList(oaslist, 'component', 'name'))
    #     return subcomponents

    def addOAS(self, oasnodes):
        #TODO see what to do with nodelists. Maybe these should be explicitly
        # linked to boundary conditions, or something else
        pass

    def genericUnpack(self, unpacklist):
        if isinstance(unpacklist[0], str):
            if hasattr(self.idfelem, unpacklist[0]):
                subcomponents = self.getListElements(unpacklist)
            else:
                subcomponents = unpacklist
        else:
            subcomponents = unpacklist

        #self.addPredicate("hasPart", subcomponents)
        return subcomponents

    def unpackStorage(self, storagelist):
        # Keep this method separate just in case we encounter edge cases down the line
        self.manualPredicate({"predicate": "hasPart", "elements": storagelist})
        return self.genericUnpack(storagelist)

    def unpackReheatSystem(self, reheatlist):
        # Keep this method separate just in case we encounter edge cases down the line
        self.manualPredicate({"predicate": "hasPart", "elements": reheatlist})
        return self.genericUnpack(reheatlist)

    def unpackFanCoilSystem(self, fancoillist):
        # Keep this method separate just in case we encounter edge cases down the line
        self.manualPredicate({"predicate": "hasPart", "elements": fancoillist})
        return self.genericUnpack(fancoillist)

    def zoneEquipment(self, equiplist):
        self.zoneequip = self.unpackList({"list" : equiplist, "type_" : 'zone_equipment', "attr_": 'name'})
        self.manualPredicate({"predicate": "isLocationOf", "elements": self.zoneequip})
        
    def manualPredicate(self, params):
        if isinstance(params, list):
            for param in params:
                self.addPredicate(param["predicate"], self.getListElements(param["elements"]))
        else:
            self.addPredicate(params["predicate"], self.getListElements(params["elements"]))

    def dualSetpoint(self, schedules):
        #TODO see how to use the TimeSeriesReference BRICK type
        pass

    def getSetpoint(self, schedules):
        #TODO see how to use the TimeSeriesReference BRICK type
        pass

    def directAdd(self, elements):
        return elements

    def extensibleMethod(self, mdict):
        subcomponents = []
        for meth in mdict:
            if hasattr(self, meth["method"]):
                mth = getattr(self, meth["method"])
                unpacked = self.unpackList({"list" : self.idfelem, "type_" : meth["type_"], "attr_": meth["attr_"]})
                if "predicate" in meth.keys():
                    extendedlist = None
                    self.manualPredicate({"predicate": meth["predicate"], "elements": unpacked})
                else:
                    extendedlist = mth(unpacked)
                if extendedlist is not None:
                    subcomponents.extend(extendedlist)

        return subcomponents

