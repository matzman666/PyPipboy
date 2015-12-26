# -*- coding: utf-8 -*-

import socket
import socketserver
import threading
import logging
import struct
import time
from .network import NetworkMessage
from .dataencoder import DataUpdateEncoder
from .types import eMessageType


class RelayController:
    class _AutodiscoverServer(socketserver.UDPServer):
        def __init__(self, controller, addr, handlerClass):
            self.allow_reuse_address = True
            super().__init__(addr, handlerClass)
            self.controller = controller
            
    class _AutodiscoverRequestHandler(socketserver.BaseRequestHandler):
        def handle(self):
            controller = self.server.controller
            csocket = self.request[1]
            controller._logger.debug('Received UDP message "' + str(self.request[0]) + '" from ' + str(self.client_address))
            csocket.sendto('{"IsBusy":false,"MachineType":"PC"}'.encode(), self.client_address)
            
    class _RelayServer(socketserver.ThreadingTCPServer):
        def __init__(self, controller, addr, handlerClass):
            self.allow_reuse_address = True
            super().__init__(addr, handlerClass)
            self.controller = controller
            self.keepAliveThreadFlag = True
            self.keepAliveThread = threading.Thread(target=self._sendKeepAlives)
            self.keepAliveThread.start()
        def _sendKeepAlives(self):
            try:
                while self.keepAliveThreadFlag:
                    time.sleep(1)
                    for h in self.controller.handlers:
                        h.sendKeepAlive()
            except Exception as e:
                print('Caught Exception: ' + str(e))
        def shutdown(self):
            self.keepAliveThreadFlag = False
            self.keepAliveThread.join()
            super().shutdown()
            
    class _RelayRequestHandler(socketserver.BaseRequestHandler):
        def handle(self):
            self.controller = self.server.controller
            self.datamanager = self.controller.datamanager
            self.controller.handlers.append(self)
            self.controller._logger.info('Added relay endpoint ' + str(self.client_address))
            self._sendConnectionAccept()
            self._sendInitialData()
            self._shutdownHandler = False
            
            while not self._shutdownHandler:
                # First receive message header, should be 5 bytes
                expected = 5
                msg_header = bytes()
                try:
                    while expected > 0:
                        tmp = self.request.recv(expected)
                        if len(tmp) == 0:
                            raise Exception('Host terminated connection.')
                        expected -= len(tmp)
                        msg_header = msg_header + tmp
                except Exception as e:
                    print('Exception caught: ' + str(e))
                    break
                # Parse header
                payload_size = struct.unpack("<I",msg_header[0:4])[0]
                msg_type = struct.unpack("<B",bytes([msg_header[4]]))[0]
                # Receive payload
                expected = payload_size
                payload = bytes()
                try:
                    while expected > 0:
                        tmp = self.request.recv(expected)
                        if len(tmp) == 0:
                            raise Exception('Host terminated connection.')
                        expected -= len(tmp)
                        payload = payload + tmp
                except Exception as e:
                    print('Exception caught: ' + str(e))
                    break
                # Send everything that is not a keep-alive message to the game
                if not msg_type == eMessageType.KEEP_ALIVE:
                    self.controller._logger.debug("Relaying client message with type %i and size %i.", msg_type, payload_size)
                    self.datamanager.networkchannel.sendMessage(NetworkMessage(msg_type, payload_size, payload))
            try:
                self.controller.handlers.remove(self)
            except:
                pass
            self.controller._logger.info('Removed relay endpoint ' + str(self.client_address))
            
        def _sendConnectionAccept(self):
            if self.datamanager.networkchannel.hostLang:
                lang = self.datamanager.networkchannel.hostLang
            else:
                lang = 'xx'
            if self.datamanager.networkchannel.hostVersion:
                version = self.datamanager.networkchannel.hostVersion
            else:
                version = '1.1.30.0' # Everything other than a version number crashes the official app
            msgtext = ('{"lang":"' + str(lang) + '","version":"' + str(version) + '"}').encode()
            msg = NetworkMessage(eMessageType.CONNECTION_ACCEPTED, len(msgtext), msgtext)
            self.datamanager.networkchannel.sendMessage(msg, self.request)
            
        def sendKeepAlive(self):
            self.datamanager.networkchannel.sendMessage(NetworkMessage(eMessageType.KEEP_ALIVE), self.request)
        
        def sendMessage(self, msg):
            self.datamanager.networkchannel.sendMessage(msg, self.request)
        
        def _sendInitialData(self):
            data = self.datamanager.exportData()
            if len(data) > 0:
                data.reverse()
                encoder = DataUpdateEncoder()
                msgtext = encoder.encode(data)
                self.datamanager.networkchannel.sendMessage(NetworkMessage(eMessageType.DATA_UPDATE, len(msgtext), msgtext), self.request)
            
            
    
    def __init__(self, datamanager):
        self.datamanager = datamanager
        self.autodiscoverThread = None
        self.autodiscoverServer = None
        self.relayServer = None
        self.relayThread = None
        self.handlers = []
        self._logger = logging.getLogger('pypipboy.relayserver')
        self.datamanager.networkchannel.registerMessageListener(self._onMessageReceived)
    
    def startAutodiscoverService(self, addr = '', port = 28000):
        if not self.autodiscoverThread:
            self.autodiscoverServer = self._AutodiscoverServer(self, (addr, port), self._AutodiscoverRequestHandler)
            self.autodiscoverServer.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, True)
            self.autodiscoverThread = threading.Thread(target=self.autodiscoverServer.serve_forever)
            self.autodiscoverThread.start()
    
    def stopAutodiscoverService(self):
        if self.autodiscoverThread:
            self.autodiscoverServer.shutdown()
            self.autodiscoverThread.join()
            self.autodiscoverServer = None
            self.autodiscoverThread = None
            
    def startRelayService(self, addr = '', port = 27000):
        if not self.relayThread:
            self.relayServer = self._RelayServer(self, (addr, port), self._RelayRequestHandler)
            self.relayThread = threading.Thread(target=self.relayServer.serve_forever)
            self.relayThread.start()
    
    def stopRelayService(self):
        if self.relayThread:
            self.relayServer.shutdown()
            self.relayThread.join()
            self.relayServer = None
            self.relayThread = None
            self.handlers.clear()
    
    def _onMessageReceived(self, msg):
        if msg.msgType != eMessageType.KEEP_ALIVE and msg.msgType != eMessageType.LOCAL_MAP_UPDATE:
            for h in self.handlers:
                h.sendMessage(msg)
    
    
    def join(self):
        if self.autodiscoverThread:
            self.autodiscoverThread.join()
        if self.relayThread:
            self.relayThread.join()

