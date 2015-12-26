# -*- coding: utf-8 -*-

import socket
import json
import threading
import time
import logging
import queue
import struct
from pypipboy.types import eMessageType



# Represents an application level network message
class NetworkMessage:
    def __init__(self, msgType, payloadSize = 0, payload = None):
        self.msgType = msgType
        self.payloadSize = payloadSize
        self.payload = payload



# Implements the network client
class NetworkChannel:

    AUTODISCOVER_MESSAGE = b'{"cmd": "autodiscover"}'
    AUTODISCOVER_ADDR = b'<broadcast>'
    AUTODISCOVER_PORT = 28000
    AUTODISCOVER_TIMEOUT = 3
    
    PIPBOYAPP_PORT = 27000
    
    KEEP_ALIVE_TIMER = 2
    
    # Constructor
    def __init__(self):
        self._data_socket = None
        self.isConnected = False
        self._receiveThread = None
        self._receiveThreadFlag = False
        self._receiveThreadRunning = False
        self._dispatchThread = None
        self._dispatchThreadFlag = False
        self._dispatchThreadRunning = False
        self._messageQueue = None
        self._connectionListeners = set()
        self._messageListeners = set()
        self._aboutToConnect = False
        self.hostLang = None
        self.hostVersion = None
        self._logger = logging.getLogger('pypipboy.network.channel')
        
    # Returns a list of dicts representing the discovered hosts 
    # (list entry example: {'MachineType': 'PC', 'addr': '192.168.168.27', 'IsBusy': False}")
    @staticmethod
    def discoverHosts(addr = AUTODISCOVER_ADDR, port = AUTODISCOVER_PORT, timeout = AUTODISCOVER_TIMEOUT):
        logger = logging.getLogger('pypipboy.network.autodiscover')
        # Open and configure Broadcast UDP socket
        dis_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        dis_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, True)
        dis_sock.settimeout(timeout)
        # Send autodiscovery message
        dis_sock.sendto(NetworkChannel.AUTODISCOVER_MESSAGE, (addr, port))
        # Listen for answers and add responding hosts to list
        retval = list()
        try:
            while True:
                data, addr = dis_sock.recvfrom(1024)
                if len(data) > 0:
                    try:
                        resp_data = json.loads(data.decode('utf-8'))
                        resp_data['addr'] = addr[0]
                        retval.append(resp_data)
                        logger.info("Found host %s", addr[0])
                    except:
                        logger.warn('Received bogus data from %s', addr)
                else:
                    logger.warn('Received bogus data from %s', addr)
        except:
            pass
        dis_sock.close()
        return retval
    
    # Connects to the given address
    # Returns True if connection was successfully established, otherwise False
    def connect(self, addr, port = PIPBOYAPP_PORT):
        if not self.isConnected:
            self._aboutToConnect = True
            try:
                # Open connection
                data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._data_socket = data_socket
                data_socket.settimeout(10)
                data_socket.connect((addr, port)) 
                # Reveice host message header, should be 5 bytes
                expected = 5
                msg_header = bytes()
                try:
                    while expected > 0:
                        tmp = data_socket.recv(expected)
                        if len(tmp) == 0:
                            raise Exception('Host terminated connection.')
                        expected -= len(tmp)
                        msg_header = msg_header + tmp
                except Exception as e:
                    self._doLostConnection(-1, str(e))
                self._aboutToConnect = False
                if len(msg_header) == 5:
                    # Parse header
                    payload_size = struct.unpack("<I",msg_header[0:4])[0]
                    msg_type = struct.unpack("<B",bytes([msg_header[4]]))[0]
                    # Reveice payload
                    payload = bytes()
                    expected = payload_size
                    while expected > 0:
                        tmp = data_socket.recv(expected)
                        expected -= len(tmp)
                        payload = payload + tmp
                    # Check success
                    if msg_type == eMessageType.CONNECTION_ACCEPTED:
                        resp = json.loads(payload.decode("utf-8"))
                        self._logger.info('Successfully connected to %s:%i.', addr, port)
                        self._logger.info('Host Version: %s.', resp['version'])
                        self._logger.info('Host Language: %s.', resp['lang'])
                        self.hostAddr = addr
                        self.hostPort = port
                        self.hostLang = resp['lang']
                        self.hostVersion = resp['version']
                        return self._doEstablishedConnection(data_socket)
                    elif msg_type == eMessageType.CONNECTION_REFUSED:
                        data_socket.close()
                        self._logger.info('Host %s:%i denied connection.', addr, port)
                        return False
                    else:
                        data_socket.close()
                        self._logger.info('Received unknown message type %i.', msg_type)
                        return False
                else:
                    self._logger.info('Received bogus message from host %s:%i.', addr, port)
                    return False
            except Exception as e:
                self._aboutToConnect = False
                raise e
        else:
            return False
    
    # Cancels an ongoing connection attempt
    def cancelConnectionAttempt(self):
        if self._aboutToConnect:
            try:
                self._data_socket.shutdown(socket.SHUT_RDWR)
            except:
                pass
 
    #Disconnects the current connection
    def disconnect(self):
        if self.isConnected:
            self._doLostConnection()
        
    # sends an message over the network
    def sendMessage(self, msg, socket = None):
        if socket or self.isConnected:
            data = struct.pack("<I", msg.payloadSize) + struct.pack("<B", msg.msgType)
            if msg.payload and len(msg.payload) > 0:
                data = data + msg.payload
            if not socket and msg.msgType != 0:
                self._logger.debug('Sending message: %s', data)
            if socket:
                socket.send(data)
            else:
                self._data_socket.send(data)

    # Registers a connection event listener
    def registerConnectionListener(self, listener):
        self._connectionListeners.add(listener)
        
    # Unregisters a connection event listener
    def unregisterConnectionListener(self, listener):
        try:
            self._connectionListeners.remove(listener)
        except:
            pass
            
    # Registers a message event listener
    def registerMessageListener(self, listener, msg_type = None):
        self._messageListeners.add((msg_type, listener))
        
    # Unregisters a message event listener
    def unregisterMessageListener(self, listener, msg_type = None):
        try:
            self._messageListeners.remove((msg_type, listener))
        except:
            pass
    
    # Internal function executed after a application level connection has been established
    def _doEstablishedConnection(self, socket):
        self.isConnected = True
        self._messageQueue = queue.Queue()
        self._receiveThreadFlag = True
        self._receiveThread = threading.Thread(target = self._receiveMessageLoop)
        self._receiveThread.start()
        self._dispatchThreadFlag = True
        self._dispatchThread = threading.Thread(target = self._dispatchMessageLoop)
        self._dispatchThread.start()
        self._fireConnectionEvent(True, 0, '')
        return True
    
    # Internal function executed after connection has been lost
    # errstatus: 0 - no error, voluntarily closed
    #           >0 - error code
    def _doLostConnection(self, errstatus = 0, errmsg = None):
        self.isConnected = False
        self._receiveThreadFlag = False
        if self._data_socket:
            self._data_socket.close()
            self._data_socket = None
        self._dispatchThreadFlag = False
        self._messageQueue.put(None)
        self._fireConnectionEvent(False, errstatus, errmsg)
        return True
        
    # Internal function emitting connection events to listeners    
    # status: True - connection established, False - connection lost
    # errstatus != 0 is bad
    def _fireConnectionEvent(self, status, errstatus, errmsg):
        for listener in self._connectionListeners:
            listener(status, errstatus, errmsg)
    
    # Internal function emitting message events to listeners    
    def _fireMessageEvent(self, msg):
        for listener in self._messageListeners:
            if listener[0] == None or listener[0] == msg.msgType:
                listener[1](msg)
        
    # Internal thread function for receiving messages
    def _receiveMessageLoop(self):
        self._logger.debug("Starting receive thread.")
        self._receiveThreadRunning = True
        lastKeepAliveTime = time.time()
        #self._data_socket.settimeout(10)
        while self._receiveThreadFlag:
            # First receive message header, should be 5 bytes
            expected = 5
            msg_header = bytes()
            try:
                while expected > 0:
                    tmp = self._data_socket.recv(expected)
                    if len(tmp) == 0:
                        raise Exception('Host terminated connection.')
                    expected -= len(tmp)
                    msg_header = msg_header + tmp
            except Exception as e:
                if self._receiveThreadFlag:
                    self._doLostConnection(-1, str(e))
                break
            # Parse header
            payload_size = struct.unpack("<I",msg_header[0:4])[0]
            msg_type = struct.unpack("<B",bytes([msg_header[4]]))[0]
            # Receive payload
            expected = payload_size
            payload = bytes()
            try:
                while expected > 0:
                    tmp = self._data_socket.recv(expected)
                    if len(tmp) == 0:
                        raise Exception('Host terminated connection.')
                    expected -= len(tmp)
                    payload = payload + tmp
            except Exception as e:
                if self._receiveThreadFlag:
                    self._doLostConnection(-1, str(e))
                break
            if msg_type != 0:
                self._logger.debug("Received message with type %i and size %i.", msg_type, payload_size)
            if msg_type == eMessageType.KEEP_ALIVE:
                # Keep Alive works as follows:
                # The Server does not like it when I send a keep alive too early
                # Both server and client regularly send keep alives messages, when no other messages are send.
                # This means that the server may not send a keep alive message for a long time when enough other
                # messages are send. 
                # The server cuts the connection when no keep alive was received for some time.
                # Thus I use following keep alive strategy here.
                # When I receive a keep alive from the server, I send one back.
                # I keep a timer that runs out after some time, and is reset whenever I send a keep alive.
                # "hen a non keep-alive package has been received and the timer has run out, I send a keep alive
                self.sendMessage(NetworkMessage(eMessageType.KEEP_ALIVE))
                lastKeepAliveTime = time.time()
            else:
                # Put message into message queue
                self._messageQueue.put(NetworkMessage(msg_type, payload_size, payload))
                # Check keep alive timer
                if lastKeepAliveTime + self.KEEP_ALIVE_TIMER < time.time():
                    self.sendMessage(NetworkMessage(eMessageType.KEEP_ALIVE))
                    lastKeepAliveTime = time.time()
        self._logger.debug("Shutting down receive thread.")
        self._receiveThreadRunning = False
                    
        
    
    # Internal thread function for dispatching received message events
    def _dispatchMessageLoop(self):
        self._logger.debug("Starting dispatch thread.")
        self._dispatchThreadRunning = True
        while self._dispatchThreadFlag:
            msg = self._messageQueue.get(True)
            if msg:
                self._logger.debug("Dispatching message with type %i and size %i", msg.msgType, msg.payloadSize)
            #try:
            if msg == None: # just a wake-up call
                pass
            elif msg.msgType == eMessageType.DATA_UPDATE:
                self._fireMessageEvent(msg)
            elif msg.msgType == eMessageType.LOCAL_MAP_UPDATE:
                self._fireMessageEvent(msg)
            elif msg.msgType == eMessageType.COMMAND_RESULT:
                self._fireMessageEvent(msg)
            else:
                self._logger.error('Received unknown message type %i.', msg.msgType)
            #except Exception as e:
            #    self._logger.error('Exception caught while handling message: %s', e)
            self._messageQueue.task_done()
        self._dispatchThreadRunning = False
        self._logger.debug("Shutting down dispatch thread.")
        
    def join(self):
        if self._receiveThread:
            self._receiveThread.join()
        if self._dispatchThread:
            self._dispatchThread.join()
