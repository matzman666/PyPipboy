
```python
class eValueUpdatedEventType:
    NEW = 0
    UPDATED = 1
    DELETED = 2

class PipboyDataManager:
    # object representing the current network connection
    networkchannel    
    
    # Returns a list of dicts representing the discovered hosts 
    # (list entry example: {'MachineType': 'PC', 'addr': '192.168.168.27', 'IsBusy': False}")
    @staticmethod
    def discoverHosts(addr = NetworkChannel.AUTODISCOVER_ADDR, port = NetworkChannel.AUTODISCOVER_PORT, timeout = NetworkChannel.AUTODISCOVER_TIMEOUT)
    
    # Connects to the given address
    # Returns True if connection was successfully established, otherwise False
    def connect(self, addr, port = NetworkChannel.PIPBOYAPP_PORT):
        
    # Cancels an ongoing connection attempt
    def cancelConnectionAttempt(self)
    
    #Disconnects the current connection
    def disconnect(self)
    
    # Waits till the current connection is closed
    def join(self)
    
    # registers a listener that gets called when a new root object becomes available
    #
    # signature: listener(rootobject)
    def registerRootObjectListener(self, listener)
        
    # unregisters a root objecct listener
    def unregisterRootObjectListener(self, listener)
    
    # registers a value updated listener
    #
    # signature: listener(value, eventtype)
    #     eventtype: see eValueUpdatedEventType
    def registerValueUpdatedListener(self, listener)
        
    # unregisters a value updated listener
    def unregisterValueUpdatedListener(self, listener)
    
    # registers a local map listener
    #
    # signature: listener(lmap)
    def registerLocalMapListener(self, listener)
        
    # unregisters a local map listener
    def unregisterLocalMapListener(self, listener)
    
    # Sets the custom marker on the map
    def rpcSetCustomMarker(self, x, y)
    
    # Removes the custom marker
    def rpcRemoveCustomMarker(self)
    
    # Let the player fast travel to the given location.
    # pipValue must be a value from the '/Map/World/Locations' array
    # Resp: {'allowed': true/false, 'success': true/false}
    def rpcFastTravel(self, pipValue, callback = None)
        
    # Sends a clear idle request
    def rpcSendClearIdleRequest(self)
    
    # Switches to the given radio station
    # pipValue must be an entry from the 'Radio' array
    def rpcToggleRadioStation(self, pipValue)
    
    Toggles the given quest active/inactive
    # pipValue must be an entry from the 'Quests' array
    def rpcToggleQuestActive(self, pipValue)
    
    # Tags the given component
    # pipValue must be an entry from the '/Inventory/InvComponents' array
    def rpcToggleComponentFavorite(self, pipValue)
    
    # Uses the given item on the player
    # pipValue must be an item from the 'Inventory' branch
    def rpcUseItem(self, pipValue)
        
    # Uses Stimpak on the player
    def rpcUseStimpak(self)
    
    # Uses RadAway on the player
    def rpcUseRadAway(self)
        
    # Drops the given item
    # pipValue must be an item from the 'Inventory' branch
    def rpcDropItem(self, pipValue, count)
    
    # Requests a local map update
    def rpcRequestLocalMapSnapshot(self)
    
    # Sets the favorite key for the given item
    # pipValue must be an item from the 'Inventory' branch
    def rpcSetFavorite(self, pipValue, quickKeySlot)
    
    # Sets the inventory sort function
    # resp: unknown
    def rpcSortInventory(self, index, callback = None)
```