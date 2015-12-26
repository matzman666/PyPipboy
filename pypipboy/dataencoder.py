# -*- coding: utf-8 -*-

import struct
from pypipboy.types import eValueType


class DataEncoder:
    def _encodeBool(self, value):
        return struct.pack("<?",value)
        
    def _encodeInt8(self, value):
        return struct.pack("<b",value)
        
        
    def _encodeUInt8(self, value):
        return struct.pack("<B",value)
        
        
    def _encodeInt16(self, value):
        return struct.pack("<h",value)
        
        
    def _encodeUInt16(self, value):
        return struct.pack("<H",value)
        
        
    def _encodeInt32(self, value):
        return struct.pack("<i",value)
        
        
    def _encodeUInt32(self, value):
        return struct.pack("<I",value)
        
        
    def _encodeFloat(self, value):
        return struct.pack("<f",value)
        
        
    def _encodeString(self, value):
        # Strings are null-terminated
        retval = b''
        count = 0
        for c in value:
            retval += c.encode()
        retval += b'\x00'
        return retval
  


class DataUpdateEncoder(DataEncoder):
    
    def encode(self, objects):
        retval = b''
        i = 0
        for o in objects:
            id = o[0]
            valuetype = o[1]
            value = o[2]
            # First byte is value type
            retval += struct.pack("<B",valuetype)
            # Next 4 bytes are pipboyValueId
            retval += struct.pack("<I",id)
            # Encode actual value
            # Parse actual value
            if valuetype == eValueType.BOOL:
                retval += self._encodeBool(value)
            elif valuetype == eValueType.INT_8:
                retval += self._encodeInt8(value)
            elif valuetype == eValueType.UINT_8:
                retval += self._encodeUInt8(value)
            elif valuetype == eValueType.INT_32:
                retval += self._encodeInt32(value)
            elif valuetype == eValueType.UINT_32:
                retval += self._encodeUInt32(value)
            elif valuetype == eValueType.FLOAT:
                retval += self._encodeFloat(value)
            elif valuetype == eValueType.STRING:
                retval += self._encodeString(value)
            elif valuetype == eValueType.ARRAY:
                retval += self._encodeArray(value)
            elif valuetype == eValueType.OBJECT:
                retval += self._encodeObject(value)
            i += 1
        return retval
            
    def _encodeArray(self, value):
        retval = b''
        # First two bytes are element count
        retval += self._encodeUInt16(len(value))
        for id in value:
            retval += self._encodeUInt32(id)
        return retval
    
    def _encodeObject(self, value):
        retval = b''
        # Objects consist of (key, value) pairs
        # First two bytes are number of added value ids
        retval += self._encodeUInt16(len(value[0]))
        for param in value[0]:
            retval += self._encodeUInt32(param[1])
            retval += self._encodeString(param[0])
        # Two bytes are number of remoced value ids
        retval += self._encodeUInt16(0)
        return retval
