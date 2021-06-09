# -*- coding: utf-8 -*-

import sys
import struct
from pypipboy.types import eValueType


class DataUpdateRecord:
    def __init__(self, id, type, value):
        self.id = id
        self.type = type
        self.value = value
    


class LocalMapUpdate:
    def __init__(self, width, height, nw, ne, sw, pixels):
        self.width = width
        self.height = height
        self.nw = nw
        self.ne = ne
        self.sw = sw
        self.pixels = pixels


class DataParser:
    def _parseBool(self):
        value = struct.unpack("<?",bytes([self.data[self.offset]]))[0]
        self.offset += 1
        return value
        
        
    def _parseInt8(self):
        value = struct.unpack("<b",bytes([self.data[self.offset]]))[0]
        self.offset += 1
        return value
        
        
    def _parseUInt8(self):
        value = struct.unpack("<B",bytes([self.data[self.offset]]))[0]
        self.offset += 1
        return value
        
        
    def _parseInt16(self):
        value = struct.unpack("<h",self.data[self.offset:self.offset+2])[0]
        self.offset += 2
        return value
        
        
    def _parseUInt16(self):
        value = struct.unpack("<H",self.data[self.offset:self.offset+2])[0]
        self.offset += 2
        return value
        
        
    def _parseInt32(self):
        value = struct.unpack("<i",self.data[self.offset:self.offset+4])[0]
        self.offset += 4
        return value
        
        
    def _parseUInt32(self):
        value = struct.unpack("<I",self.data[self.offset:self.offset+4])[0]
        self.offset += 4
        return value
        
        
    def _parseFloat(self):
        value = struct.unpack("<f", self.data[self.offset:self.offset+4])[0]
        self.offset += 4
        return value
        
        
    def _parseString(self):
        # Strings are null-terminated
        count = 0
        while self.data[self.offset + count ] != 0:
            count += 1
        value = self.data[self.offset:self.offset + count].decode(sys.getdefaultencoding(), 'replace')
        self.offset += count + 1
        return value
  


class DataUpdateParser(DataParser):
    def parse(self, data, callback):
        #print("\n Parsing data message:")
        self.offset = 0
        self.data = data
        # Parse individual Records
        while self.offset < len(data):
            # First byte is value type
            valuetype = struct.unpack("<B",bytes([self.data[self.offset]]))[0]
            self.offset += 1
            # Next 4 bytes are pipboyValueId (Bethesda also calls them nodeID)
            nodeID = struct.unpack("<I",self.data[self.offset:self.offset+4])[0]
            self.offset += 4
            # Parse actual value
            if valuetype == eValueType.BOOL:
                value = self._parseBool()
                #print(str(nodeID) + " => bool: " + str(value))
            elif valuetype == eValueType.INT_8:
                value = self._parseInt8()
                #print(str(nodeID) + " => int8: " + str(value))
            elif valuetype == eValueType.UINT_8:
                value = self._parseUInt8()
                #print(str(nodeID) + " => uint8: " + str(value))
            elif valuetype == eValueType.INT_32:
                value = self._parseInt32()
                #print(str(nodeID) + " => int32: " + str(value))
            elif valuetype == eValueType.UINT_32:
                value = self._parseUInt32()
                #print(str(nodeID) + " => uint32: " + str(value))
            elif valuetype == eValueType.FLOAT:
                value = self._parseFloat()
                #print(str(nodeID) + " => float: " + str(value))
            elif valuetype == eValueType.STRING:
                value = self._parseString()
                #print(str(nodeID) + " => string: " + str(value))
            elif valuetype == eValueType.ARRAY:
                value = self._parseArray()
                #print(str(nodeID) + " => array: " + str(value))
            elif valuetype == eValueType.OBJECT:
                value = self._parseObject()
                #print(str(nodeID) + " => object: " + str(value))
            callback(DataUpdateRecord(nodeID, valuetype, value))
        
        
    def _parseArray(self):
        # First two bytes are element count
        count = self._parseUInt16()
        value = list()
        for i in range(0, count):
            # An Array only consists of pipboyValueIDs
            value.append(self._parseUInt32())
        return value
        
        
    def _parseObject(self):
        # Objects consist of (key, value) pairs
        # First two bytes are number of added value ids
        added_count = self._parseUInt16()
        added = list()
        for i in range(0, added_count):
            # pipboyValueID as value
            valueid = self._parseUInt32()
            # string as key
            key = self._parseString()
            added.append((key, valueid))
        # Two bytes are number of remoced value ids
        removed_count = self._parseUInt16()
        removed = list()
        for i in range(0, removed_count):
            # 4 Bytes value id
            valueid = self._parseUInt32()
            removed.append(valueid)
        return (added, removed)
 
 
 
class LocalMapUpdateParser(DataParser):
    def parse(self, data):
        self.offset = 0
        self.data = data
        # first is width
        width = self._parseUInt32()
        # next is width
        height = self._parseUInt32()
        # then we have the map extends
        nw = (self._parseFloat(), self._parseFloat())
        ne = (self._parseFloat(), self._parseFloat())
        sw = (self._parseFloat(), self._parseFloat())
        # the rest we leave as it is
        return LocalMapUpdate(width, height, nw, ne, sw, self.data[self.offset:])
