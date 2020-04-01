import sys
from alfalfaclient import AlfalfaClient

client = AlfalfaClient(url='http://web')
result = client.submit('/test/SmallOffice_Unitary_1.osm')

# Replace with test framework
if result:
    print("success")
    sys.exit(0)
else:
    print("failure")
    sys.exit(1)
