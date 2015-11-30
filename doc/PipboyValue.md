
```python
class ePipboyValueType:
    PRIMITIVE = 0,
    OBJECT = 1
    ARRAY = 2
    
class PipboyValue(object):

    # Unique identifier
    pipId
    
    # value type (see ePipboyValueType)
    pipType
    
    # Tree parent (of type PipboyValue)
    pipParent
    
    # Key used by the parent to access this value
    pipParentKey
    
    # The parents index with its parent
    pipParentIndex
    
    # registers a value updated event listener
    #    depth: to with depth should events from children be reported
    #
    # signature: listener(caller, value, pathobj)
    #    caller: who called the callback
    #    value: changed value
    #    pathobj: list of values lying on the path from event origin to reporter
    def registerValueUpdatedListener(self, listener, depth = 0)
    
    # registers a value updated event listener
    def unregisterValueUpdatedListener(self, listener)
    
    # Returns the value
    def value(self)
    
    # Returns the number of children
    def childCount(self)
    
    # Returns the child with given key/index (returned objects are of type PipboyValue)
    def child(self, key)
    
    # Returns the key for the item with the given key (returned objects are of type string for objects and int for arrays)
    def key(self, index)
    
    # Returns a string representation of the tree path
    def pathStr(self)
```