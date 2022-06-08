#!/usr/bin/env python
import json
import os
import argparse
import requests

_LOCKFILE_NAME = 'lockfile'
_LOCKFILE_LOC = 'C:\Riot Games\League of Legends\\'
_LOOT_ENDPOINT = 'lol-loot/v1/player-loot'
_CRAFT_ENDPOINT = 'lol-loot/v1/recipes'
_LOOT_NAME = 'lootName'
_LOCALIZED_DESC = 'localizedDescription'
_LOOT_ID = 'lootId'
_LOOT_COUNT = 'count'
_LOOT_TYPE = 'type'
_LOOT_ITEM_DESC = 'itemDesc'
_CHAMP_RENT = 'CHAMPION_RENTAL'
_USER = 'riot'
_CLIENT_ADDRESS = 'https://127.0.0.1'
_CHEST = 'CHEST'

#Loot crafting options
_DISENCHANT = 'CHAMPION_RENTAL_disenchant'
_OPEN = '_OPEN'  #chest recipe name is <lootID>_OPEN
_CRAFT = 'craft'

#Query
_REPEAT = 'repeat='

def parser_setup():
    parser = argparse.ArgumentParser(description='Do stuff with lol loot inventory')
    parser.add_argument('-c', '--check', action='store_true', help='Only check what will be done')
    parser.add_argument('-s', '--shards', action='store_true',  help='Disenchant shards')
    parser.add_argument('-b', '--cap', action='store_true', help='Open all capsules')
    parser.add_argument('-k', '--keep', nargs='?', const=2, type=int, default=2, help='keep a certain number of shards')
    parser.add_argument('-f', '--full', action='store_true', help='Do shards and chests (combination of -s and -b)')
    return parser

# returns port # and pw
def get_secrets():
    if _LOCKFILE_NAME in os.listdir():
        _LOCKFILE = os.getcwd() + '\\' + _LOCKFILE_NAME
    else:
        _LOCKFILE = _LOCKFILE_LOC + _LOCKFILE_NAME

    if not os.path.isfile(_LOCKFILE):
        print(f'Lockfile does not exist at {_LOCKFILE}. Start League client or run this script from the same dir as the lockfile')
        exit(1)

    with open(_LOCKFILE) as _fh:
        file = _fh.readline()

    # process name : PID : port : pw : protocol
    contents = file.split(':')
    return tuple([contents[2], contents[3]])

# returns json object of player loot
def get_loot(session, address):
    result = session.get('/'.join([address, _LOOT_ENDPOINT]))
    return json.loads(result.content)

# TODO: generalize get functions into one
#returns array of dicts with ID, Name, and count
def get_chests(lootJson):
    resultArr = []
    for loot in lootJson:
        # capsules have CHEST in lootName and no localized Description
        if _CHEST in loot[_LOOT_NAME] and loot[_LOCALIZED_DESC] == '':
            lootDict = {
                _LOOT_NAME: loot[_LOOT_NAME],
                _LOOT_COUNT: loot[_LOOT_COUNT],
                _LOOT_ID: loot[_LOOT_ID]
            }
            resultArr.append(lootDict)

    return resultArr

#returns array of dicts with ID, Name, and count
def get_shards(lootJson):
    resultArr = []
    for loot in lootJson:
        if loot[_LOOT_TYPE] == _CHAMP_RENT:
            lootDict = {
                _LOOT_ITEM_DESC: loot[_LOOT_ITEM_DESC],
                _LOOT_COUNT: loot[_LOOT_COUNT],
                _LOOT_ID: loot[_LOOT_ID]
            }
            resultArr.append(lootDict)

    return resultArr

#uses loot format from get_shards
def smash_shards(session, address, loot, keep=2, check = False):
    for x in loot:
        count = int(x[_LOOT_COUNT])
        if count - keep > 0:
            use_recipe(session, address, x[_LOOT_ID], count - keep, check)

#uses loot format from get_shards
def open_capsules(session, address, loot, check = False):
    for x in loot:
        count = int(x[_LOOT_COUNT])
        use_recipe(session, address, x[_LOOT_ID], count, check)

#uses lootID to determine a recipe and then runs it for a number of times
def use_recipe(session, address, lootId, count, check = False):
    header = { 'Content-Type': 'application/json' }
    payload = '["' + lootId + '"]'

    if _CHEST in lootId:
        recipe = lootId + _OPEN
    else:
        recipe = _DISENCHANT
    
    if count > 1:
        craft = _CRAFT + '?' + _REPEAT + str(count)
    else:
        craft = _CRAFT
    
    url = '/'.join([address, _CRAFT_ENDPOINT, recipe, craft])

    if check:
        print (url + '   -   ' + lootId + '    -   ' + str(count))
        return

    response = session.post(url, headers=header, data=payload)

    if not response.status_code == 200:
        print(f'Request to {url} failed')
        exit(1)

if __name__ == "__main__":
    parser = parser_setup()
    args = parser.parse_args()
    print(args)

    _secrets = get_secrets()
    _current_address = _CLIENT_ADDRESS + ':' + _secrets[0]

    s = requests.Session()
    s.auth = (_USER,_secrets[1])
    s.verify = False

    j = get_loot(s, _current_address)

    #if an option, capsules always get opened first
    if args.cap or args.full:
        caps = get_chests(j)
        open_capsules(s, _current_address, caps, args.check)

    # if a full was done. need to re-get loot
    if args.full:
        j = get_loot(s, _current_address)
    
    if args.full or args.shards:
        shards = get_shards(j)
        smash_shards(s,_current_address, shards, args.keep, args.check)

