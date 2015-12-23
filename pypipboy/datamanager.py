# -*- coding: utf-8 -*-

import logging
import json
import threading
from pypipboy.types import eMessageType, eValueType, eRequestType
from pypipboy.dataparser import DataUpdateParser, LocalMapUpdateParser, DataUpdateRecord
from pypipboy.network import NetworkChannel, NetworkMessage



# enum of Pipboy value types
class ePipboyValueType:
    PRIMITIVE = 0,
    OBJECT = 1
    ARRAY = 2



# enum of value updated event types
class eValueUpdatedEventType:
    NEW = 0
    UPDATED = 1
    DELETED = 2



# PipboyValue base class
class PipboyValue(object):
    class _UserCacheEntry:
        def __init__(self, value, invalidateDepth):
            self.value = value
            self.invalidateDepth = invalidateDepth
            self.dirtyFlag = False
    
    # constructor
    def __init__(self, pipId, pipType, valueType, value):
        self.pipParent = None
        self.pipParentKey = None
        self.pipParentIndex = 0
        self.pipId = pipId
        self.pipType = pipType
        self.valueType = valueType
        self._value = value
        self._userCache = dict()
        self._valueUpdatedListeners = dict()
        self._listenerLock = threading.Lock()
    
    # registers a value updated event listener
    #    depth: to with depth should events from children be reported
    #
    # signature: listener(caller, value, pathobj)
    #    caller: who called the callback
    #    value: changed value
    #    pathobj: list of values lying on the path from event origin to reporter
    def registerValueUpdatedListener(self, listener, depth = 0):
        self._listenerLock.acquire()
        self._valueUpdatedListeners[listener] = depth
        self._listenerLock.release()
    
    # registers a value updated event listener
    def unregisterValueUpdatedListener(self, listener):
        self._listenerLock.acquire()
        try:
            del self._valueUpdatedListeners[listener]
        except:
            pass
        self._listenerLock.release()
    
    # Returns the value
    def value(self):
        return self._value
    
    # Returns the number of children
    def childCount(self):
        return 0
    
    # Returns the child with given key/index
    def child(self, key):
        return None
    
    # Returns the key for the item with the given key
    def key(self, index):
        return None
    
    # Returns a string representation of the value data path
    def pathStr(self):
        if self.pipParent:
            if self.pipParent.pipType == ePipboyValueType.ARRAY:
                pkey = '[' + str(self.pipParentKey) + ']'
            else:
                pkey = '/' + self.pipParentKey
            return self.pipParent.pathStr() + pkey
        else:
            return ''
    
    # Sets the user cache entry for given key to value.
    def setUserCache(self, key, value, invalidateDepth = 0):
        e = self._UserCacheEntry(value, invalidateDepth)
        self._userCache[key] = e
        return e
    
    # Returns the user cache entry for the given key or None    
    def getUserCache(self, key):
        try:
            return self._userCache[key]
        except:
            return None
         
    # Internal function emitting value updated events
    def _fireValueUpdatedEvent(self, value, pathObjs = list(), depth = 0):
        self._listenerLock.acquire()
        for k in self._userCache:
            e = self._userCache[k]
            if e.invalidateDepth <= depth:
                e.dirtyFlag = True
        for listener in self._valueUpdatedListeners:
            if self._valueUpdatedListeners[listener] < 0 or self._valueUpdatedListeners[listener] >= depth:
                listener(self, value, pathObjs)
        if self.pipParent:
            newPathObjs = list(pathObjs)
            newPathObjs.append(self)
            self.pipParent._fireValueUpdatedEvent(value, newPathObjs, depth + 1)
        self._listenerLock.release()
            
    # Overriden function to have nicer str() outputs
    def __repr__(self):
        return 'PipValue(Id=' + str(self.pipId) + ')'



# Represents a primitive value
class PipboyPrimitiveValue(PipboyValue):
    def __init__(self, pipId, valueType, value):
        super(PipboyPrimitiveValue, self).__init__(pipId, ePipboyValueType.PRIMITIVE, valueType, value)



# Represents an object value
class PipboyObjectValue(PipboyValue):
    
    def __init__(self, pipId):
        super(PipboyObjectValue, self).__init__(pipId, ePipboyValueType.OBJECT, eValueType.OBJECT, dict())
        self._orderedList = list()
        keylist = list(self._value.keys())
        keylist.sort()
        i = 0
        for r in keylist:
            self._value[r].pipParentIndex = i
            self._orderedList.append(self._value[r])
            i += 1
        
    def childCount(self):
        return len(self._value)
    
    def child(self, index):
        if type(index) == str:
            if index in self._value:
                return self._value[index]
            else:
                return None
        else:
            if index < len(self._value):
                return self._orderedList[index]
            else:
                return None
    
    def key(self, index):
        if index < len(self._value):
            return self._orderedList[index].pipParentKey
        else:
            return None



# Represents an array value
class PipboyArrayValue(PipboyValue):
    
    def __init__(self, pipId):
        super(PipboyArrayValue, self).__init__(pipId, ePipboyValueType.ARRAY, eValueType.ARRAY, list())
    
    def childCount(self):
        return len(self._value)
    
    def child(self, index):
        if index < len(self._value):
            return self._value[index]
        else:
            return None
    
    def key(self, index):
        if index < len(self._value):
            return index
        else:
            return None



class PipboyDataManager:
    
    def __init__(self):
        self.networkchannel = NetworkChannel()
        self._connectionEstablished = False
        self._valueMap = None
        self.rootObject = None
        self._rootObjectListeners = set()
        self._valueUpdatedListeners = set()
        self._localMapListeners = set()
        self.networkchannel.registerConnectionListener(self._onConnectionStateChange)
        self.networkchannel.registerMessageListener(self._onMessageReceived)
        self._nextRpcReqId = 0
        self._rpcCallbackMap = dict()
        self._logger = logging.getLogger('pypipboy.datamanager')
        
    
    # Returns a list of dicts representing the discovered hosts 
    # (list entry example: {'MachineType': 'PC', 'addr': '192.168.168.27', 'IsBusy': False}")
    @staticmethod
    def discoverHosts(addr = NetworkChannel.AUTODISCOVER_ADDR, port = NetworkChannel.AUTODISCOVER_PORT, timeout = NetworkChannel.AUTODISCOVER_TIMEOUT):
        return NetworkChannel.discoverHosts(addr, port, timeout)
    
    # Connects to the given address
    # Returns True if connection was successfully established, otherwise False
    def connect(self, addr, port = NetworkChannel.PIPBOYAPP_PORT):
        return self.networkchannel.connect(addr, port)
        
    # Cancels an ongoing connection attempt
    def cancelConnectionAttempt(self):
        return self.networkchannel.cancelConnectionAttempt()
    
    #Disconnects the current connection
    def disconnect(self):
        return self.networkchannel.disconnect()
    
    def join(self):
        return self.networkchannel.join()
    
    # registers a listener that gets called when a new root object becomes available
    #
    # signature: listener(rootobject)
    def registerRootObjectListener(self, listener):
        self._rootObjectListeners.add(listener)
        
    # unregisters a root objecct listener
    def unregisterRootObjectListener(self, listener):
        try:
            self._rootObjectListeners.remove(listener)
        except:
            pass
    
    # registers a value updated listener
    #
    # signature: listener(value, eventtype)
    def registerValueUpdatedListener(self, listener):
        self._valueUpdatedListeners.add(listener)
        
    # unregisters a value updated listener
    def unregisterValueUpdatedListener(self, listener):
        try:
            self._valueUpdatedListeners.remove(listener)
        except:
            pass
    
    # registers a local map listener
    #
    # signature: listener(lmap)
    def registerLocalMapListener(self, listener):
        self._localMapListeners.add(listener)
        
    # unregisters a local map listener
    def unregisterLocalMapListener(self, listener):
        try:
            self._localMapListeners.remove(listener)
        except:
            pass
    
    # Returns the value with the given pipId
    def getPipValueById(self, pipId):
        try:
            return self._valueMap[pipId]
        except:
            return None
    

    def rpcSendRequest(self, reqtype, args = list(), callback = None):
        if  self._connectionEstablished:
            req = dict()
            req['id'] = self._nextRpcReqId
            self._nextRpcReqId += 1
            req['type'] = reqtype
            req['args'] = list()
            if args:
                for arg in args:
                    req['args'].append(arg)
            msg = json.dumps(req).encode('utf-8')
            if callback:
                self._rpcCallbackMap[req['id']] = callback
            self.networkchannel.sendMessage(NetworkMessage(eMessageType.COMMAND, len(msg), msg))
    
    
    def rpcSetCustomMarker(self, x, y):
        thirdarg = True # Dunno what this is, the original source says: this.currentTab == 1 ? 1 : 0
        self.rpcSendRequest(eRequestType.SetCustomMapMarker, [float(x), float(y), thirdarg])
    
    def rpcRemoveCustomMarker(self):
        self.rpcSendRequest(eRequestType.RemoveCustomMapMarker)
    
    # pipValue must be a value from the '/Map/World/Locations' array
    # Resp: {'allowed': true/false, 'success': true/false}
    def rpcFastTravel(self, pipValue, callback = None):
        self.rpcSendRequest(eRequestType.FastTravel, [pipValue.pipId], callback)
        
    def rpcSendClearIdleRequest(self):
        self.rpcSendRequest(eRequestType.ClearIdle)
    
    # pipValue must be an entry from the 'Radio' array
    def rpcToggleRadioStation(self, pipValue):
        self.rpcSendRequest(eRequestType.ToggleRadioStation, [pipValue.pipId])
    
    # pipValue must be an entry from the 'Quests' array
    def rpcToggleQuestActive(self, pipValue):
        if not pipValue.child('formID'):
            raise Exception('Missing formID')
        formid = pipValue.child('formID').value()
        if not pipValue.child('instance'):
            raise Exception('Missing instance')
        instance  = pipValue.child('instance').value()
        if not pipValue.child('type'):
            raise Exception('Missing type')
        qtype = pipValue.child('type').value()
        self.rpcSendRequest(eRequestType.ToggleQuestActive, [formid, instance, qtype])
    
    # pipValue must be an entry from the '/Inventory/InvComponents' array
    def rpcToggleComponentFavorite(self, pipValue):
        if not pipValue.child('componentFormID'):
            raise Exception('Missing componentFormID')
        componentFormID = pipValue.child('componentFormID').value()
        inventory = self.rootObject.child('Inventory')
        if not inventory or not inventory.child('Version'):
            raise Exception('Could not find inventory version')
        version = inventory.child('Version').value()
        self.rpcSendRequest(eRequestType.ToggleComponentFavorite, [componentFormID, version])
    
    # pipValue must be an item from the 'Inventory' branch
    def rpcUseItem(self, pipValue):
        if not pipValue.child('HandleID'):
            raise Exception('Missing HandleID')
        handleid = pipValue.child('HandleID').value()
        if not pipValue.child('StackID') or pipValue.child('StackID').childCount() <= 0:
            raise Exception('Missing StackID')
        stackid  = pipValue.child('StackID').child(0).value()
        inventory = self.rootObject.child('Inventory')
        if not inventory or not inventory.child('Version'):
            raise Exception('Could not find inventory version')
        version = inventory.child('Version').value()
        self.rpcSendRequest(eRequestType.UseItem, [handleid, stackid, version])
        
    def rpcUseStimpak(self):
        inventory = self.rootObject.child('Inventory')
        if not inventory:
            raise Exception('Could not find inventory object')
        if inventory.child('stimpakObjectIDIsValid').value():
            self.rpcUseItem(self._valueMap[inventory.child('stimpakObjectID').value()])
        else:
            raise Exception('stimpakObjectID is not valid')
        
    def rpcUseRadAway(self):
        inventory = self.rootObject.child('Inventory')
        if not inventory:
            raise Exception('Could not find inventory object')
        version = inventory.child('Version').value()
        if inventory.child('radawayObjectIDIsValid').value():
            self.rpcUseItem(self._valueMap[inventory.child('radawayObjectID').value()])
        else:
            raise Exception('radawayObjectID is not valid')
        
        
    # pipValue must be an item from the 'Inventory' branch
    def rpcDropItem(self, pipValue, count):
        if not pipValue.child('HandleID'):
            raise Exception('Missing HandleID')
        handleid = pipValue.child('HandleID').value()
        if not pipValue.child('StackID') or pipValue.child('StackID').childCount() <= 0:
            raise Exception('Missing StackID')
        stacklist = list()
        for i in pipValue.child('StackID').value():
            stacklist.append(i.value())
        inventory = self.rootObject.child('Inventory')
        if not inventory or not inventory.child('Version'):
            raise Exception('Could not find inventory version')
        version = inventory.child('Version').value()      
        self.rpcSendRequest(eRequestType.DropItem, [handleid, count, version, stacklist])
        
    def rpcRequestLocalMapSnapshot(self):        
        self.rpcSendRequest(eRequestType.RequestLocalMapSnapshot)
    
    # pipValue must be an item from the 'Inventory' branch
    def rpcSetFavorite(self, pipValue, quickKeySlot):
        if not pipValue.child('HandleID'):
            raise Exception('Missing HandleID')
        handleid = pipValue.child('HandleID').value()
        if not pipValue.child('StackID') or pipValue.child('StackID').childCount() <= 0:
            raise Exception('Missing StackID')
        stacklist = list()
        for i in pipValue.child('StackID').value():
            stacklist.append(i.value())
        inventory = self.rootObject.child('Inventory')
        if not inventory or not inventory.child('Version'):
            raise Exception('Could not find inventory version')
        version = inventory.child('Version').value()  
        self.rpcSendRequest(eRequestType.SetFavorite, [handleid, stacklist, quickKeySlot, version])
        
    # resp: unknown
    def rpcSortInventory(self, index, callback = None):
        self.rpcSendRequest(eRequestType.SortInventory, [index], callback)
    
    
    def exportData(self):
        if self.rootObject:
            pipValues = []
            queue = [self.rootObject]
            while len(queue) > 0:
                obj = queue.pop(0)
                if obj.pipType == ePipboyValueType.OBJECT:
                    value = [[], []]
                    for k in obj.value():
                        child = obj.child(k)
                        value[0].append((k, child.pipId))
                        queue.append(child)
                    pipValues.append([obj.pipId, obj.valueType, value])
                elif obj.pipType == ePipboyValueType.ARRAY:
                    value = []
                    for child in obj.value():
                        value.append(child.pipId)
                        queue.append(child)
                    pipValues.append((obj.pipId, obj.valueType, value))
                else:
                    pipValues.append((obj.pipId, obj.valueType, obj.value()))
            return pipValues
        else:
            return []
        
    def importData(self, data):
        # only import when no active connection
        if  not self._connectionEstablished:
            self._valueMap = dict()
            self.rootObject = None
            for record in data:
                self._onRecordParsed(DataUpdateRecord(record[0], record[1], record[2]))
            return True
        else:
            return False
            
        
    ######## Internals Begin ##############
        
    def _onConnectionStateChange(self, state, errstatus, errmsg):
        if state and not self._connectionEstablished:
            self._valueMap = dict()
            self.rootObject = None
            self._connectionEstablished = True
        elif not state and self._connectionEstablished:
            self._connectionEstablished = False
    
    def _onMessageReceived(self, msg):
        if msg.msgType == eMessageType.DATA_UPDATE:
            parser = DataUpdateParser();
            parser.parse(msg.payload, self._onRecordParsed)
        elif msg.msgType == eMessageType.COMMAND_RESULT:
            resp = json.loads(msg.payload.decode())
            if resp['id'] in self._rpcCallbackMap:
                self._rpcCallbackMap[resp['id']](resp)
                del self._rpcCallbackMap[resp['id']]
            else:
                self._logger.debug('Command Result: ' + str(resp))
        elif msg.msgType == eMessageType.LOCAL_MAP_UPDATE:
            parser = LocalMapUpdateParser();
            lmap = parser.parse(msg.payload)
            self._fireLocalMapUpdatedEvent(lmap)
        
    def _onRecordParsed(self, record):
        obj = None
        recordExists = record.id in self._valueMap
        if recordExists:
            obj = self._valueMap[record.id]
        if record.type == eValueType.OBJECT:
            if not recordExists:
                obj = PipboyObjectValue(record.id)
            for r in record.value[0]:
                if not r[1] in self._valueMap:
                    raise RuntimeError('Tangling reference ' + str(r[1]))
                child = self._valueMap[r[1]]
                child.pipParent = obj
                child.pipParentKey = r[0]
                obj._value[r[0]] = child
            i = 0
            keylist = list(obj._value.keys())
            keylist.sort()
            obj._orderedList.clear()
            for r in keylist:
                obj._value[r].pipParentIndex = i
                obj._orderedList.append(obj._value[r])
                i += 1
            for r in record.value[1]:
                if r in self._valueMap:
                    v = self._valueMap[r]
                    self._logger.debug(str(v) + '[' + v.pathStr() + '] marked for deletion.')
                    # Just to delete the objects here leads to random crashes in the GUI
                    # ToDo: Need some clever mechanism to delete stale objects
                    #self._valueMap.pop(r)
            if not recordExists:
                self._valueMap[record.id] = obj
                if record.id == 0:
                    self.rootObject = obj
                    self._onRootObjectKnown()
        elif record.type == eValueType.ARRAY:
            if not recordExists:
                obj = PipboyArrayValue(record.id)
            else:
                obj._value = list()
            i = 0
            for r in record.value:
                if not r in self._valueMap:
                    raise RuntimeError('Tangling reference ' + str(r))
                child = self._valueMap[r]
                child.pipParent = obj
                child.pipParentKey = i
                child.pipParentIndex = i
                obj._value.append(child)
                i += 1
            if not recordExists:
                self._valueMap[record.id] = obj
        else:
            if recordExists:
                obj._value = record.value
            else:
                obj = PipboyPrimitiveValue(record.id, record.type, record.value)
                self._valueMap[record.id] = obj
        if recordExists:
            eventtype = eValueUpdatedEventType.UPDATED
        else:
            eventtype = eValueUpdatedEventType.NEW
        self._fireValueUpdatedEvent(obj, eventtype)
        if recordExists:
            obj._fireValueUpdatedEvent(obj)
                
    
    
    def _onRootObjectKnown(self):
        self._fireRootObjectEvent(self.rootObject)
        #self.printJSON()
        
    
    def _fireRootObjectEvent(self, rootObject):
        for listener in self._rootObjectListeners:
            listener(rootObject)
        
    
    def _fireValueUpdatedEvent(self, value, eventtype):
        for listener in self._valueUpdatedListeners:
            listener(value, eventtype)
        
    
    def _fireLocalMapUpdatedEvent(self, lmap):
        for listener in self._localMapListeners:
            listener(lmap)


        