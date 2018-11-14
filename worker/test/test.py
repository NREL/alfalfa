import os
directory = "/test/output"
if not os.path.exists(directory):
    os.makedirs(directory)

file = open("/test/output/output.txt","w") 
file.write("Hello World") 
file.close()
