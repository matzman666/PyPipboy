
![python_version](https://img.shields.io/badge/Python-3.0-green.svg) ![license_gpl3](https://img.shields.io/badge/License-GPL%203.0-green.svg)

# PyPipboy

PyPipboy is a Python3 module implementing an event-driven, rich client for the Fallout 4 Companion App protocol. 

It connects to a running Fallout 4 game ([www.fallout4.com](https://www.fallout4.com/)) (using the Companion App interface) and receives data from the game. 
This data can then be accessed using an event-driven interface. Furthermore it can also send commands to the game.

[PyPipboyApp](https://github.com/matzman666/PyPipboyApp) is a GUI application build on top of PyPipboy.

# Features

Currently implemented features are:
 - Autodiscovery
 - Connection Handling
 - Receiving Data Updates and Local Map Updates
 - Sending Commands (RPC)
 
# Current Status

PyPipboy is feature complete, but still in alpha state.


# Usage

First create an PipboyDataManager object.

```python
from pypipboy.datamanager import PipboyDataManager
pipboy = PipboyDataManager()
```

Then register a root object listener.

```python
def rootObjectListener(rootObject):
   .... # Do something with the root object
```

Then connect to the game.

```python
pipboy.connect('localhost')
```

When the library connects to the game it sends data which is organized in form of a tree. 
As soon as the root of the tree is known (meaning the tree is fully parsed and there are no tangling references), a root object event is fired.
Inside the event handle you can interact with the root object, traverse the tree, register additional listener, ...

For example, navigating to the player's current health and registering a listener for value changes is done like this:

```python
def currHpListener(caller, pipvalue, pathObjs):
    ... # Do something
    
def rootObjectListener(rootObject):
    currHP = rootObject.child('PlayerInfo').child('CurrHP')
    currHP.registerValueUpdatedListener(currHpListener)
```
To navigate to a specific value inside the tree, start from the top and navigate down on known paths. For example, to fetch an array with all map location markers, start with the root element you got from the root object event and retrieve the child 'Map'. Then, from the map object retrieve the child 'World', and finally 'Locations'. In short: rootObject.child('Map').child('World').child('Locations'). But don't forget to check whether a certain element already exists. For example, if the user stills linger around in the main menu and hasn't loaded a save at all, there is no 'World' object and you would get an exception. 

When the user loads a new save, most values get invalidated and don't receive any events anymore. You need to fetch the new elements and re-register the event listeners with them. To know that the user loaded a new save, you need to register listeners with the parents (or their parents) of the values. It is not always easy to say (with the 'Locations' it is the 'Map' object) which parent persists a save load. I have also written another application "PyPipboyApp" (see link above), that allows you to browse the data and see the data updates. Use it to find out which value persists a save load.

# API references

 - [PipboyDataManager](doc/PipboyDataManager.md)
 - [PipboyValue](doc/PipboyValue.md)
 - [NetworkChannel](doc/NetworkChannel.md)


# Known bugs

It is in alpha state, there might be bugs.

# Contribution

Everyone who wants to contribute is welcome.

# How did I learn about the protocol?

By re-engineering the official Fallout 4 Companion App (the Android version). 
The file assets/bin/Data/Managed/Assembly-CSharp.dll contains all code related to the protocol.
I just fired up my favorite C#-Disassembler, disassembled that file and read the source code.

# License

This software is released under GPL 3.0.

