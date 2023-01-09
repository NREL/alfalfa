import sys
import brickschema
from brickschema.namespaces import BRICK
from rdflib import Namespace, RDFS, RDF, URIRef, Graph

def main(argv):

    graph = Graph()
    BRICK = Namespace('https://brickschema.org/schema/Brick#') #1.0.1 is not supported anymore
    BF = Namespace('https://brickschema.org/schema/Brick#') #BrickFrame -> BRICK
    EX = Namespace('http://eptobrick.com#')
    graph.bind('brick', BRICK)
    #self.graph.bind('brick', self.BF)
    graph.bind('rdfs', RDFS)
    graph.bind('rdf', RDF)
    graph.bind('ep2b', EX)
    graph.parse(argv[0], format='turtle') # Load the stored graph.

    points = []
    for s, p, o in graph.triples((None, RDF['type'], BRICK['Temperature_Sensor'])):
        points.extend([s.split('#')[-1].replace('&58', ':').replace('%20', ' ')])
    for s, p, o in graph.triples((None, RDF['type'], BRICK['Temperature_Setpoint'])):
        points.extend([s.split('#')[-1].replace('&58', ':').replace('&20', ' ')])
    print(points)
    return points

if __name__ == "__main__":
   main(sys.argv[1:])