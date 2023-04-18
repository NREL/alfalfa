import sys
from brickschema.namespaces import BRICK
from rdflib import Namespace, RDFS, RDF, Graph, URIRef

def main(argv):

    graph = Graph()
    BRICK = Namespace('https://brickschema.org/schema/Brick#') #1.0.1 is not supported anymore
    BF = Namespace('https://brickschema.org/schema/Brick#') #BrickFrame -> BRICK
    EX = Namespace('http://eptobrick.com#')
    graph.bind('brick', BRICK)
    graph.bind('rdfs', RDFS)
    graph.bind('rdf', RDF)
    graph.bind('ep2b', EX)
    graph.parse(argv[0], format='turtle') # Load the stored graph.

    keys = []
    vars = []
    supportedsensors = ["Temperature_Sensor", "Pressure_Sensor", "Humidity_Sensor", "Air_Flow_Sensor", "Enthalpy_Sensor", "Zone_Air_Temperature_Sensor", "Zone_Air_Humidity_Sensor"]
    supportedsetpoints = ["Temperature_Setpoint", "Humidity_Setpoint", "Air_Flow_Setpoint", "Heating_Temperature_Setpoint", "Cooling_Temperature_Setpoint", "Zone_Air_Humidity_Setpoint"]
    for sensor in supportedsensors:
        for s in graph.subjects(RDF['type'], BRICK[sensor]):
            #tag = graph.objects(s, BRICK['hasTag'])
            keys.append(formatname(s))#graph.qname(s) if isinstance(s, URIRef) else s, end=" "))
            vars.append(sensor)
        #points.extend([formatname(s)])
    for setpoint in supportedsetpoints:
        for s in graph.subjects(RDF['type'], BRICK[setpoint]):
            #tag = graph.objects(s, BRICK['hasTag'])
            keys.append(formatname(s))#graph.qname(s) if isinstance(s, URIRef) else s, end=" "))
            vars.append(setpoint)
            #points.extend([formatname(s)])
    print(keys, vars)
    return keys, vars

def formatname(name):
    return str(name).split('#')[-1].replace('&58', ':').replace('&20', ' ')

if __name__ == "__main__":
   main(sys.argv[1:])