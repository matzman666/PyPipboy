# -*- coding: utf-8 -*-

#
# Dumps the received data in json format and exits
#

from pypipboy.datamanager import PipboyDataManager, ePipboyValueType



pipboy = PipboyDataManager()



def toJSON(pipvalue, padding = ''):
    s = str()
    if pipvalue.pipType == ePipboyValueType.OBJECT:
        s += '{\n'
        for k in pipvalue.value():
            s += padding + '  "' + k + '": ' + toJSON(pipvalue.child(k), padding + '  ') + '\n'
        s += padding + '},'
        return s
    elif pipvalue.pipType == ePipboyValueType.ARRAY:
        s += '[\n'
        for k in pipvalue.value():
            s += padding + '  ' + toJSON(k, padding + '  ') + '\n'
        s += padding + '],'
        return s
    else:
        return str(pipvalue.value())



# This callback will be executed as soon as the initial data tree has been completely parsed.
# The argument is the PipboyValue instance representing the root of the tree
def rootObjectListener(rootObject):
    print(toJSON(rootObject)) # Recursively print the tree
    pipboy.disconnect() # Close connection to exit application



hosts = pipboy.discoverHosts()
if len(hosts) > 0:
    pipboy.registerRootObjectListener(rootObjectListener)
    pipboy.connect(hosts[0]['addr']) # Connect to first found host
    if pipboy.connect(hosts[0]['addr']): # Connect to first found host
        pipboy.join() # Wait till connection has been closed
    else:
        print('Host denied connection.')
else:
    print('No hosts found.')

