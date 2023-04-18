

# Add I/O for alfalfa from BRICK

## Description
This method adds inputs and outputs for Alfalfa and generates a metadata model that follows the BRICK ontology.

## Modeler Description
The OpenStudio workspace is saved to an IDF in a temporary folder. The measure calls a Python library that parses the IDF and infers the type of components and their parents/children. This information is recorded in a Turtle file using the BRICK ontology. This measure reads the Turtle file and assigns all the necessary input/output bindings for Alfalfa and the BCVTB and saves the new workspace.

## Measure Type
EnergyPlusMeasure

## Taxonomy


## Arguments
