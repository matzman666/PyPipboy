# -*- coding: utf-8 -*-

#
# Runs in an infinite loop and prints all received value updates to the console
#

from pypipboy.datamanager import PipboyDataManager, eValueUpdatedEventType
from pypipboy.types import eValueType



pipboy = PipboyDataManager()



# This callback will be executed for every new/updated/deleted value
# The argument is the PipboyValue instance representing the changed value and
# the event type
def valueUpdatedListener(value, eventtype):
    txt = str()
    if eventtype == eValueUpdatedEventType.NEW:
        txt += 'New'
    elif eventtype == eValueUpdatedEventType.UPDATED:
        txt += 'Updated'
    else:
        txt += 'Deleted'
    txt += ' Record(' + str(value.pipId) + '): ' 
    if eventtype != eValueUpdatedEventType.NEW:
        txt += value.pathStr() + ' => '
    if value.valueType == eValueType.BOOL:
        txt += 'bool( '
    elif value.valueType == eValueType.INT_8:
        txt += 'int8( '
    elif value.valueType == eValueType.UINT_8:
        txt += 'uint8( '
    elif value.valueType == eValueType.INT_32:
        txt += 'int32( '
    elif value.valueType == eValueType.UINT_32:
        txt += 'uint32( '
    elif value.valueType == eValueType.FLOAT:
        txt += 'float( '
    elif value.valueType == eValueType.STRING:
        txt += 'string( '
    elif value.valueType == eValueType.ARRAY:
        txt += 'array( '
    elif value.valueType == eValueType.OBJECT:
        txt += 'object( '
    txt += str(value.value()) + ' )'
    print(txt)



hosts = pipboy.discoverHosts()
if len(hosts) > 0:
    pipboy.registerValueUpdatedListener(valueUpdatedListener)
    if pipboy.connect(hosts[0]['addr']): # Connect to first found host
        pipboy.join() # Wait till connection has been closed
    else:
        print('Host denied connection.')
else:
    print('No hosts found.')

