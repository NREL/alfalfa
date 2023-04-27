import sys
try:
    from brickschema.namespaces import BRICK
except:
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", 'brickschema'])
    from brickschema.namespaces import BRICK
try:
    from rdflib import Namespace, RDFS, RDF, Graph, URIRef
except:
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", 'rfdlib'])
    from rdflib import Namespace, RDFS, RDF, Graph, URIRef

BRICK = Namespace('https://brickschema.org/schema/Brick#')
EX = Namespace('http://eptobrick.com#')

def getGraph(path):
    graph = Graph()
    graph.bind('brick', BRICK)
    graph.bind('rdfs', RDFS)
    graph.bind('rdf', RDF)
    graph.bind('ep2b', EX)
    graph.parse(path, format='turtle') # Load the stored graph.
    return graph

def request(graph, s, p, o):
    spo = [None, None, None]
    for i, e in enumerate([s, p, o]):
        spl = e.split(':')
        if 'brick' in spl:
            spo[i] = BRICK[spl[-1]]
        elif 'rdf' in spl:
            spo[i] = RDF[spl[-1]]
        elif e != 'None':
             spo[i] = EX[e]
    res = []
    for t in graph.triples(tuple(spo)):
        res.append([formatname(i) for i in t])
    return res


def main(argv):

    graph = getGraph(argv[0])
    res = request(graph, argv[1], argv[2], argv[3])
    print(res)

def formatname(name):
    return str(name).split('#')[-1].replace('&58', ':').replace('&20', ' ')

if __name__ == "__main__":
   main(sys.argv[1:])