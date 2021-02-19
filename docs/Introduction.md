# Introduction to Alfalfa

The main goals of Alfalfa include the following:
1.	Provide a RESTful interface for co-simulation through which an OpenStudio/EnergyPlus or Modelica model can be interacted with.  Alfalfa supports upload of osw, fmu, or zip (a zipped-up version of the OpenStudio workflow directory structure) files.
2.	Support large-scale parallel building simulation using commodity cloud computing resources such as AWS.
3.	To convert model objects (such as fans, airloops, sensing points, etc.) into Haystack entities using the Haystack metadata model.
4.	Expose these Haystack entities via the Haystack API to enable ‘virtual’ buildings to be interacted with in a similar manner to an actual building.
5.	Provide a RESTful interface for uploading, starting, and stopping simulation(s), as well as a simple user interface for these tasks.



