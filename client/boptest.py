class Boptest:

    # The url argument is the address of the Boptest server
    # default should be http://localhost:8080/api
    def __init__(self, url):

    # The path argument should be a filesystem path to an fmu
    # this should be equivalent to uploading a file through 
    # Boptest UI. See code here 
    # https://github.com/NREL/alfalfa/blob/develop/web/components/Upload/Upload.js#L127
    # return value should be a string unique identifier for the model
    def submit(self, path):

    # Start a simulation for model identified by id. The id should corrsespond to 
    # a return value from the submit method
    # sim_params should be parameters such as start_time, end_time, timescale,
    # and others. The details need to be further defined and documented
    def start(self, id, **sim_params):

    # Stop a simulation for model identified by id
    def stop(self, id):

    # Return the input values for simulation identified by id,
    # in the form of a dictionary. See setInputs method for dictionary format
    def inputs(self, id):

    # Set inputs for model identified by id
    # The inputs argument should be a dictionary of 
    # with the form
    # inputs = {
    #  input_name: { level_1: value_1, level_2: value_2...},
    #  input_name2: { level_1: value_1, level_2: value_2...}
    # }
    def setInputs(self, id, **inputs):

    # Return a dictionary of the output values
    # result = {
    # output_name1 : output_value1,
    # output_name2 : output_value2
    #}
    def outputs(self, id):
