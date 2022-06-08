#!/usr/bin/env python
_LOCKFILE_LOC = "/c/Riot Games/League of Legends/lockfile"
_LOCKFILE_LOC2 = 'C:\Riot Games\League of Legends\lockfile'

with open(_LOCKFILE_LOC2) as _fh:
    file = _fh.readline()

# process name : PID : port : pw : protocol
contents = file.split(':')

print('Port - ' + contents[2])
print('PW - ' + contents[3])