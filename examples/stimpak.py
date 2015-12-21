# -*- coding: utf-8 -*-

#
# Runs in an infinite loop and watches the current health of the player
# When the health falls below 50.0, a stimpak is automatically applied
#

from pypipboy.datamanager import PipboyDataManager



pipboy = PipboyDataManager()



def currHpListener(caller, pipvalue, pathObjs):
    print('CurrHp changed: ', pipvalue.value())
    if pipvalue.value() <= 50.0:
        print('Stimpak applied')
        pipboy.rpcUseStimpak()



# This callback will be executed as soon as the initial data tree has been completely parsed.
# The argument is the PipboyValue instance representing the root of the tree
def rootObjectListener(rootObject):
    playerInfo = rootObject.child('PlayerInfo')
    if playerInfo:
        # Whenever the player loads a new game, the "currHP" object we are about to fetch 
        # gets invalidated and we don't receive any event anymore.
        # Therefore we also register an listener with the "PlayerInfo" object.
        playerInfo.registerValueUpdatedListener(playerInfoReset)
        currHp = playerInfo.child('CurrHP')
        if currHp:
            print('Current Health: ', currHp.value())
            currHp.registerValueUpdatedListener(currHpListener)
        else:
            print('No Health Info found')
    else:
        print('No PlayerInfo found')

# Save was loaded (or something else that caused to game to reset).
# Refetch player health value and re-register listener.
def playerInfoReset(caller, pipvalue, pathObjs):
        currHp = pipvalue.child('CurrHP')
        if currHp:
            print('Current Health: ', currHp.value())
            currHp.registerValueUpdatedListener(currHpListener)
        else:
            print('No Health Info found')
    
    


hosts = pipboy.discoverHosts()
print('hosts: ', hosts)
if len(hosts) > 0:
    pipboy.registerRootObjectListener(rootObjectListener)
    if pipboy.connect(hosts[0]['addr']): # Connect to first found host
        pipboy.join() # Wait till connection has been closed
    else:
        print('Host denied connection.')
else:
    print('No hosts found.')

