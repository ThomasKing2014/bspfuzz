#!/usr/bin/env python2
import shutil
import struct
import os
from subprocess import check_output

startpoint = int(check_output("nm bspfuzz | grep startpoint | cut -d' ' -f1", shell=True), 16)

shutil.copyfile('bin/dedicated.orig.so', 'bin/dedicated.so')
shutil.copyfile('bin/engine.orig.so', 'bin/engine.so')
shutil.copyfile('bin/libtier0.orig.so', 'bin/libtier0.so')

def patch(d, offset, s):
    d[offset:offset+len(s)] = s

######### engine.so
dat = bytearray(open("bin/engine.orig.so").read())

# Jump to forkserver entry point after initialization.
# 0x286d20 is the NET_CloseAllSockets function.
patch(dat, 0x286D20,
    (
    '\xb8' + struct.pack('<I', startpoint) +  # mov eax, startpoint
    '\xff\xd0'                                # call eax
    ))

# Patch out a function that is registered via atexit().
# You can find it by looking for the single xref to the string
# "Missing shutdown function for %s"
patch(dat, 0x2CCDB0, "\xc3")

# nop out a call to BeginWatchdogTimer in the initialization sequence, so that we
# don't get SIGABRT after a while
patch(dat, 0x263F5F, "\x90"*6)

with open("bin/engine.so", "wb") as f:
  f.write(dat)

######### libtier0.so
dat = bytearray(open("bin/libtier0.orig.so").read())

# Avoid Plat_ExitPlatform crash
# .text:000156E7                 test    ebx, ebx
# .text:000156E9                 jz      short loc_156F5
# .text:000156EB                 mov     ds:dword_0, 1
patch(dat, 0x156E7, "\x90"*(0x156F5-0x156e7))
with open("bin/libtier0.so", "wb") as f:
  f.write(dat)
