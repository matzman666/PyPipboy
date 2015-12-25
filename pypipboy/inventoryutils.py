# -*- coding: utf-8 -*-

# Retrieve all inventory items matching filterFunc
def inventoryGetItems(inventory, filterFunc = None):
    retval = []
    sortedIds = inventory.child('sortedIDS')
    if sortedIds:
        for id in sortedIds.value():
            item = inventory.datamanager.getPipValueById(id.value())
            if item and not filterFunc or filterFunc(item):
                retval.append(item)
    return retval

# Retrieve first inventory item matching filterFunc
def inventoryGetItem(inventory, filterFunc):
    sortedIds = inventory.child('sortedIDS')
    if sortedIds:
        for id in sortedIds.value():
            item = inventory.datamanager.getPipValueById(id.value())
            if item and not filterFunc or filterFunc(item):
                return item
    return None

# ItemCardInfo ValueType parameter
class eItemCardInfoValueType:
    Int = 0
    String = 1
    Float = 2

# ItemCardInfo text parameter
class eItemCardInfoValueText:
    Value = '$val'
    Weight = '$wt'
    Accuracy = '$acc'
    Range = '$rng'
    RateOfFire = '$ROF'
    Damage = '$dmg'
    Speed = '$speed'
    DamageResist = '$dr'

# ItemCardInfo damageType parameter for both weapons and apparel (#10 is weapon only)
class eItemCardInfoDamageType:
    Physical = 1
    Poison = 2
    Unknown3 = 3
    Energy = 4
    Unknown5 = 5
    Radiation = 6
    Ammunition = 10 # (diverting from intended use, Bethesda?)

# Returns all matching ItemCardInfo entries
def itemFindItemCardInfos(item, matchValue, matchKey = 'text'):
    retval = []
    infos = item.child('itemCardInfoList')
    for i in infos.value():
        if i.child(matchKey).value() == matchValue:
            retval.append(i)
    return retval

# Returns the first matching ItemCardInfo entry
def itemFindItemCardInfo(item, matchValue, matchKey = 'text'):
    infos = item.child('itemCardInfoList')
    for i in infos.value():
        value = i.child(matchKey)
        if value and value.value() == matchValue:
            return i
    return None

# Returns the first matching ItemCardInfo value (values are cached)
def itemFindItemCardInfoValue(item, matchValue, matchKey = 'text', valueKey = 'Value'):
    cachekey = 'ici_' + str(matchValue) + str(matchKey) + str(valueKey)
    cached = item.getUserCache(cachekey)
    if not cached or cached.dirtyFlag:
        vInfo = itemFindItemCardInfo(item, matchValue, matchKey)
        if vInfo:
            try:
                value = vInfo.child(valueKey).value()
                item.setUserCache(matchValue, cachekey, 10)
            except:
                value = None
        else:
            value = None
    else:
        value = cached.value
    return value


# item Filter Categories (filterFlag parameter)
# Items can have more than one category (bit-wise or)
# e.g. holotape_item = Misc | Holotape
class eItemFilterCategory:
    Favorite = (1<<0) # 1
    Weapon = (1<<1) # 2
    Apparel = (1<<2) # 4
    Aid = (1<<3) # 8
    Book = (1<<7) # 128
    Misc = (1<<9) # 512
    Junk = (1<<10) # 1024
    Mods = (1<<11) # 2048
    Ammo = (1<<12) # 4096
    Holotape = (1<<13) # 8192

# Return whether the item has any of the given filter categories
def itemHasAnyFilterCategory(item, categories):
    if item.child('filterFlag').value() & categories:
        return True
    return False

# Return whether the item has the exact given filter categories
def itemHasExactFilterCategory(item, categories):
    if item.child('filterFlag').value() == categories:
        return True
    return False

# Returns whether the item is a key
def itemIsAKey(item):
    if item.pipParent.pipParentKey == '47':
        return True
    return False

# Returns whether the item is a gun
# A gun is a weapon with range > 0 and ammunition (damagetype = 10)
def itemIsWeaponGun(item):
    if itemHasAnyFilterCategory(item, eItemFilterCategory.Weapon):
        range = itemFindItemCardInfoValue(item, eItemCardInfoValueText.Range)
        if (type(range) == float and range > 0.0 
                and itemFindItemCardInfoValue(item, 10, 'damageType', 'damageType')):
            return True
    return False

# Returns whether the item is a melee weapon
# A melee weapon is a weapon with has a speed value
def itemIsWeaponMelee(item):
    if itemHasAnyFilterCategory(item, eItemFilterCategory.Weapon):
        if itemFindItemCardInfoValue(item, eItemCardInfoValueText.Speed):
            return True
    return False

# Returns whether the item is a throwable weapon
# A throwable weapon is a weapon with has RateOfFire == 0
def itemIsWeaponThrowable(item):
    if itemHasAnyFilterCategory(item, eItemFilterCategory.Weapon):
        rof = itemFindItemCardInfoValue(item, eItemCardInfoValueText.RateOfFire)
        if type(rof) == float and rof == 0.0:
            return True
    return False
    

