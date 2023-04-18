import os, json
from itertools import combinations
from rdflib import Namespace, RDFS, RDF, Graph
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'common'))
import epcomponent as epc
m = epc.m

class Extractor(epc.Extractor):

    def __init__(self, verbose=3) -> None:
        super(Extractor, self).__init__()
        self.graph = Graph()
        self.BRICK = Namespace('https://brickschema.org/schema/Brick#') #1.0.1 is not supported anymore
        self.EX = Namespace('http://eptobrick.com#')
        self.graph.bind('brick', self.BRICK)
        self.graph.bind('rdfs', RDFS)
        self.graph.bind('rdf', RDF)
        self.graph.bind('ep2b', self.EX)

        with open(os.path.join(os.path.dirname(__file__), 'brickMap.json')) as f:
            brickmap = json.load(f)
        self.mergeBindings(brickmap)

    def addPredicates(self):

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

        print (f"Found {count} connections.")

    def cleanupPredicates(self):
        for component in self.components.values():
            m.printMessage(f"{component.name}, a {component.btype}", lvl='debug')
            if not isinstance(component, Point):
                for predicate in component.bpredicates.keys():
                    for obj in component.bpredicates[predicate]:
                        if hasattr(obj, "name"):
                            if not isinstance(obj, Component):
                                m.printMessage(f"Converting {obj.name} to a eptobrick component.")
                                found = False
                                for cobj in self.components.values():
                                    if (cobj.idfelem == obj):
                                        component.bpredicates[predicate] = [i for i in component.bpredicates[predicate] if i != obj]
                                        obj = cobj
                                        component.bpredicates[predicate].append(obj)
                                        found = True
                                        break
                                    m.printMessage(f"Warning! Could not find component matching {obj.name} or type {epc.getEPType(obj)}", lvl='error')

                            try:
                                m.printMessage(f"\t{predicate} {obj.name}, a {self.components[obj.name].btype}", lvl='debug')
                            except KeyError:
                                m.printMessage(f"\t{predicate} {obj.name}, which does not have a BRICK type yet", lvl='warning')
                        else:
                            m.printMessage(f"Warning! In {component.name} {predicate} {obj}: could not find {obj}")
        for component in self.components.values():
            if not isinstance(component, Point):
                self.components[component.name] = self.fixPredicates(component)

    def fixPredicates(self, comp):
        
        nextinline = []
        cont = False
        m.printMessage(f"Fixing {comp.name}", lvl='debug')
        while not cont:
            cont = True
            for predicate in comp.bpredicates.keys():
                for obj in comp.bpredicates[predicate]:
                    if not hasattr(obj, "btype"):
                        obj = self.components[obj]
                    if obj.btype == "" and obj.bpredicates != {}:
                        m.printMessage(f"Found empty object: {obj.name}")
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

    def getComponent(self, element, nodelists):
        res = []
        epcomponent = Component(element, nodelists)
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
                            res.extend(self.getComponent(subc, nodelists))
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

    def addPoints(self):
        # Add all setpoint and sensor points, assuming that each outlet has 
        # Sensors:
        # System Node + 
        #   Temperature,
        #   Relative Humidity [%]
        #   Pressure [Pa]
        #   Standard Density Volume Flow Rate [m3/s]
        #   Enthalpy [J/kg]
        connections = 0
        points = 0 
        newcomponents = {}
        for component in self.components.values():
            if component.btype in ['AHU', 'CAV', 'VAV', 'RVAV', 'Terminal_Unit']:
                # inout = component.inlets + component.outlets
                inout = component.outlets
                
                if inout != []:
                    m.printMessage(f"Adding points to {len(inout)} nodes in {component.name}.", lvl='debug')
                for conn in inout:
                    connections += 1
                    if conn is None:
                        break # See entry for WaterHeater:Mixed in commonMap.json. Some inlets/outlets are not properly assigned and appear as None.
                    for bsensors in ["Temperature_Sensor", "Pressure_Sensor", "Humidity_Sensor", "Air_Flow_Sensor", "Enthalpy_Sensor"]:
                        newcomponents[f"{conn}_{bsensors}"] = Point(f"{conn}_{bsensors}", bsensors, component)
                        points += 1
                    # keep sensors and setpoints separate until fully debugged
                    for bstp in ["Temperature_Setpoint", "Humidity_Setpoint", "Air_Flow_Setpoint"]:
                        newcomponents[f"{conn}_{bstp}"] = Point(f"{conn}_{bstp}", bstp, component)
                        points += 1
                
            if component.btype == 'Zone':
                for bsensors in ["Zone_Air_Temperature_Sensor", "Zone_Air_Humidity_Sensor"]:
                        newcomponents[f"{component.name}_{bsensors}"] = Point(f"{component.name}_{bsensors}", bsensors, component)
                        points += 1
                for bstps in ["Heating_Temperature_Setpoint", "Cooling_Temperature_Setpoint"]:#, "Zone_Air_Humidity_Setpoint"]:
                        newcomponents[f"{component.name}_{bstps}"] = Point(f"{component.name}_{bstps}", bstps, component)
                        points += 1
                

            
        for key in newcomponents.keys():
            self.components[key] = newcomponents[key]
        m.printMessage(f"Found {connections} systems and added {points} points.", lvl='debug')

    def createGraph(self):
        for subj in self.components.values():
            if subj.btype != "":
                self.graph.add((self.EX[self.legalizeURI(subj.name)], RDF['type'], self.BRICK[subj.btype]))
                for predicate in subj.bpredicates.keys():
                    for obj in subj.bpredicates[predicate]:
                        self.graph.add((self.EX[self.legalizeURI(subj.name)], self.BRICK[predicate], self.EX[self.legalizeURI(obj.name)]))

    def legalizeURI(self, uri):
        return uri.replace(':', '&58').replace(' ', '&20')

    def saveGraph(self, outname=None):
        if outname is None:
            outname = self.outname
        self.graph.serialize(destination=f'{outname}.ttl', format='turtle')
        return self.graph

class Point(epc.Point):
    def __init__(self, name, btype, parent) -> None:
        super(Point, self).__init__(name, btype, parent)
        self.btype = btype
        self.bpredicates = {"isPointOf": [parent]}

        # Need inlets and outlets for the connectComponents method.
        self.inlets = []
        self.outlets = []

    def update(self, other):
        m.printMessage(f"Updating {self.name}. Checking for conflicts.", lvl="debug")
        if self.name == other.name:
            for pred in other.bpredicates.keys():
                if pred not in self.bpredicates.keys():
                    self.bpredicates[pred] = other.bpredicates[pred]
                else:
                    self.bpredicates[pred].extend([i for i in other.bpredicates[pred] if i not in self.bpredicates[pred]])
            m.printMessage(f"Successfully updated {self.name}", lvl="success")
        else:
            raise Exception(f"Error while updating {self.name} (an EP {self.etype}) with values from {other.name}: conflicts exist", lvl="failure")

class Component(epc.Component):
    def __init__(self, idfelem, nodelists) -> None:
        super(Component, self).__init__(idfelem, nodelists)
        self.btype = None
        self.bpredicates = {}

    def assignBasics(self, bindings):
        self.btype = bindings["BrickType"]
        super(Component, self).assignBasics()

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

    # def addInlets(self, inlets):
    #     super(Component, self).addInlets(inlets)
    #     for inlet in inlets:
    #         self.addPoints(inlet)
    
    # def addOutlets(self, outlets):
    #     super(Component, self).addOutlets(outlets)
    #     for outlet in outlets:
    #         self.addPoints(outlet)

    # def addNodes(self, nodes):
    #     super(Component, self).addNodes(nodes)
    #     for node in nodes:
    #         self.addPoints(node)

    def addNodelist(self, nodelists):
        if "inlet" in nodelists.keys():
            for nodelist in nodelists["inlet"]:
                self.manualPredicate({"predicate": "isFedBy", "elements": [nodelist]})
                return getattr(self.idfelem, nodelist)
                ## TODO: this returns a string, not an idf element. Why?
        if "outlet" in nodelists.keys():
            for nodelist in nodelists["outlet"]:
                self.manualPredicate({"predicate": "feeds", "elements": [nodelist]})
                return getattr(self.idfelem, nodelist)

    def addPredicate(self, predicate, elements):
        for element in elements:
            try:
                # we need this try/except, because somehow the hasattr() method returns always False
                ## getattr(element, "name")
                if predicate in self.bpredicates.keys():
                    self.bpredicates[predicate].extend([element for element in elements if element not in self.bpredicates[predicate]])
                else:
                    self.bpredicates[predicate] = [element for element in elements]
            except:
                pass

    def unpackList(self, params):
        res = super(Component, self).unpackList(params)
        #self.addPredicate("hasPart", res)
        return res

    def unpackBranch(self, branchnames):
        subcomponents = []
        for branch in branchnames:
            bsc = self.unpackList({"list" : branch, "type_" : 'component', "attr_": 'name'})
            subcomponents.extend(bsc)
        self.addPredicate("hasPart", subcomponents)
        return subcomponents

    def unpackBranchList(self, branchlistnames):
        branchlists = self.getListElements(branchlistnames)
        subcomponents = []
        for branchlist in branchlists:
            branches = self.unpackList({"list" : branchlist, "type_" : 'branch', "attr_": 'name'})
            self.unpackBranch(branches)
        return subcomponents

    def addOAS(self, oasnodes):
        #TODO see what to do with nodelists. Maybe these should be explicitly
        # linked to boundary conditions, or something else
        pass

    def genericUnpack(self, unpacklist):
        subcomponents = super(Component, self).genericUnpack(unpacklist)
        self.addPredicate("hasPart", subcomponents)
        return subcomponents

    def unpackStorage(self, storagelist):
        # Keep this method separate just in case we encounter edge cases down the line
        self.manualPredicate({"predicate": "hasPart", "elements": storagelist})
        return super(Component, self).unpackStorage(storagelist)

    def unpackReheatSystem(self, reheatlist):
        # Keep this method separate just in case we encounter edge cases down the line
        self.manualPredicate({"predicate": "hasPart", "elements": reheatlist})
        return super(Component, self).unpackReheatSystem(reheatlist)

    def unpackFanCoilSystem(self, fancoillist):
        # Keep this method separate just in case we encounter edge cases down the line
        self.manualPredicate({"predicate": "hasPart", "elements": fancoillist})
        return super(Component, self).unpackFanCoilSystem(fancoillist)

    def zoneEquipment(self, equiplist):
        super(Component, self).zoneEquipment(equiplist)
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
                m.printMessage(f"{self.name}: \tUsing method {meth['method']}", lvl='debug')
                unpacked = self.unpackList({"list" : self.idfelem, "type_" : meth["type_"], "attr_": meth["attr_"]})
                if "predicate" in meth.keys():
                    extendedlist = None
                    self.manualPredicate({"predicate": meth["predicate"], "elements": unpacked})
                else:
                    extendedlist = mth(unpacked)
                if extendedlist is not None:
                    subcomponents.extend(extendedlist)

        return subcomponents

    # def addPoints(self, node):
    #     # Add all setpoint and sensor points, assuming that each outlet has 
    #     # Sensors:
    #     # System Node + 
    #     #   Temperature,
    #     #   Relative Humidity [%]
    #     #   Pressure [Pa]
    #     #   Standard Density Volume Flow Rate [m3/s]
    #     #   Enthalpy [J/kg]
    #     # Setpoints:

    #     points = []
    #     for bsensors in ["Temperature_Sensor", "Pressure_Sensor", "Humidity_Sensor", "Air_Flow_Sensor", "Enthalpy_Sensor"]:
    #         points.append(Point(f"{node}_{bsensors}", bsensors, self))
    #     # keep sensors and setpoints separate until fully debugged
    #     for bstp in ["Temperature_Setpoint", "Pressure_Setpoint", "Humidity_Setpoint", "Air_Flow_Setpoint", "Enthalpy_Setpoint"]:
    #         points.append(Point(f"{node}_{bstp}", bstp, self))

    #     print([point.name for point in points])
        
    #     return points

