#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2018 4AM
#
# SPDX-License-Identifier: MIT

# (c) 2018 by 4am
# MIT-licensed

import argparse
import collections
import json
import os
import sys

__version__ = "1.0"
__date__ = "2018-09-08"
__progname__ = "a2rchery"
__displayname__ = __progname__ + " by 4am (" + __date__ + ")"

# chunk IDs for .a2r files
kA2R2 = b"A2R2"
kINFO = b"INFO"
kSTRM = b"STRM"
kMETA = b"META"
# other things defined in the .a2r specification
kLanguages = ("English","Spanish","French","German","Chinese","Japanese","Italian","Dutch","Portuguese","Danish","Finnish","Norwegian","Swedish","Russian","Polish","Turkish","Arabic","Thai","Czech","Hungarian","Catalan","Croatian","Greek","Hebrew","Romanian","Slovak","Ukrainian","Indonesian","Malay","Vietnamese","Other")
kRequiresRAM = ("16K","24K","32K","48K","64K","128K","256K","512K","768K","1M","1.25M","1.5M+","Unknown")
kRequiresMachine = ("2","2+","2e","2c","2e+","2gs","2c+","3","3+")
kCaptureTiming = 1
kCaptureBits = 2
kCaptureXTiming = 3

# strings and things, for print routines and error messages
sEOF = "Unexpected EOF"
sBadChunkSize = "Bad chunk size"
dNoYes = {False:"no",True:"yes"}
tQuarters = (".00",".25",".50",".75")
dTiming = {kCaptureTiming:"timing",kCaptureBits:"bits",kCaptureXTiming:"xtiming"}

# errors that may be raised
class A2RError(Exception): pass # base class
class A2REOFError(A2RError): pass
class A2RFormatError(A2RError): pass
class A2RHeaderError(A2RError): pass
class A2RHeaderError_NoA2R2(A2RHeaderError): pass
class A2RHeaderError_NoFF(A2RHeaderError): pass
class A2RHeaderError_NoLF(A2RHeaderError): pass
class A2RINFOFormatError(A2RFormatError): pass
class A2RINFOFormatError_BadVersion(A2RINFOFormatError): pass
class A2RINFOFormatError_BadDiskType(A2RINFOFormatError): pass
class A2RINFOFormatError_BadWriteProtected(A2RINFOFormatError): pass
class A2RINFOFormatError_BadSynchronized(A2RINFOFormatError): pass
class A2RINFOFormatError_BadCleaned(A2RINFOFormatError): pass
class A2RINFOFormatError_BadCreator(A2RINFOFormatError): pass
class A2RSTRMFormatError(A2RFormatError): pass
class A2RMETAFormatError(A2RFormatError): pass
class A2RMETAFormatError_DuplicateKey(A2RFormatError): pass
class A2RMETAFormatError_BadValue(A2RFormatError): pass
class A2RMETAFormatError_BadLanguage(A2RFormatError): pass
class A2RMETAFormatError_BadRAM(A2RFormatError): pass
class A2RMETAFormatError_BadMachine(A2RFormatError): pass

class A2RParseError(A2RError):
    pass

def from_uint32(b):
    return int.from_bytes(b, byteorder="little")
from_uint16=from_uint32

def to_uint32(b):
    return b.to_bytes(4, byteorder="little")

def to_uint16(b):
    return b.to_bytes(2, byteorder="little")

def to_uint8(b):
    return b.to_bytes(1, byteorder="little")

def raise_if(cond, e, s=""):
    if cond: raise e(s)

class DiskImage: # base class
    def __init__(self, filename=None, stream=None):
        raise_if(not filename and not stream, A2RError, "no input")
        self.filename = filename
        self.tracks = []

    def seek(self, track_num):
        """returns Track object for the given track, or None if the track is not part of this disk image. track_num can be 0..40 in 0.25 increments (0, 0.25, 0.5, 0.75, 1, &c.)"""
        return None

class A2RValidator:
    def validate_info_version(self, version):
        raise_if(version != b'\x01', A2RINFOFormatError_BadVersion, "Unknown version (expected 1, found %s)" % version)

    def validate_info_disk_type(self, disk_type):
        raise_if(disk_type not in (b'\x01',b'\x02'), A2RINFOFormatError_BadDiskType, "Unknown disk type (expected 1 or 2, found %s)" % disk_type)

    def validate_info_write_protected(self, write_protected):
        raise_if(write_protected not in (b'\x00',b'\x01'), A2RINFOFormatError_BadWriteProtected, "Unknown write protected flag (expected 0 or 1, found %s)" % write_protected)

    def validate_info_synchronized(self, synchronized):
        raise_if(synchronized not in (b'\x00',b'\x01'), A2RINFOFormatError_BadSynchronized, "Unknown synchronized flag (expected 0, or 1, found %s)" % synchronized)

    def validate_info_creator(self, creator_as_bytes):
        raise_if(len(creator_as_bytes) > 32, A2RINFOFormatError_BadCreator, "Creator is longer than 32 bytes")
        try:
            creator_as_bytes.decode("UTF-8")
        except:
            raise_if(True, A2RINFOFormatError_BadCreator, "Creator is not valid UTF-8")

    def encode_info_creator(self, creator_as_string):
        creator_as_bytes = creator_as_string.encode("UTF-8").ljust(32, b" ")
        self.validate_info_creator(creator_as_bytes)
        return creator_as_bytes

    def decode_info_creator(self, creator_as_bytes):
        self.validate_info_creator(creator_as_bytes)
        return creator_as_bytes.decode("UTF-8").strip()

    def validate_metadata(self, metadata_as_bytes):
        try:
            metadata = metadata_as_bytes.decode("UTF-8")
        except:
            raise A2RMETAFormatError("Metadata is not valid UTF-8")

    def decode_metadata(self, metadata_as_bytes):
        self.validate_metadata(metadata_as_bytes)
        return metadata_as_bytes.decode("UTF-8")

    def validate_metadata_value(self, value):
        raise_if("\t" in value, A2RMETAFormatError_BadValue, "Invalid metadata value (contains tab character)")
        raise_if("\n" in value, A2RMETAFormatError_BadValue, "Invalid metadata value (contains linefeed character)")
        raise_if("|" in value, A2RMETAFormatError_BadValue, "Invalid metadata value (contains pipe character)")

    def validate_metadata_language(self, language):
        raise_if(language and (language not in kLanguages), A2RMETAFormatError_BadLanguage, "Invalid metadata language")

    def validate_metadata_requires_ram(self, requires_ram):
        raise_if(requires_ram and (requires_ram not in kRequiresRAM), A2RMETAFormatError_BadRAM, "Invalid metadata requires_ram")

    def validate_metadata_requires_machine(self, requires_machine):
        raise_if(requires_machine and (requires_machine not in kRequiresMachine), A2RMETAFormatError_BadMachine, "Invalid metadata requires_machine")

class A2RReader(DiskImage, A2RValidator):
    def __init__(self, filename=None, stream=None):
        DiskImage.__init__(self, filename, stream)
        self.info = collections.OrderedDict()
        self.meta = collections.OrderedDict()
        self.flux = collections.OrderedDict()

        with stream or open(filename, "rb") as f:
            header_raw = f.read(8)
            raise_if(len(header_raw) != 8, A2REOFError, sEOF)
            self.__process_header(header_raw)
            while True:
                chunk_id = f.read(4)
                if not chunk_id: break
                raise_if(len(chunk_id) != 4, A2REOFError, sEOF)
                chunk_size_raw = f.read(4)
                raise_if(len(chunk_size_raw) != 4, A2REOFError, sEOF)
                chunk_size = from_uint32(chunk_size_raw)
                data = f.read(chunk_size)
                raise_if(len(data) != chunk_size, A2REOFError, sEOF)
                if chunk_id == kINFO:
                    raise_if(chunk_size != 36, A2RFormatError, sBadChunkSize)
                    self.__process_info(data)
                elif chunk_id == kSTRM:
                    self.__process_strm(data)
                elif chunk_id == kMETA:
                    self.__process_meta(data)

    def __process_header(self, data):
        raise_if(data[:4] != kA2R2, A2RHeaderError_NoA2R2, "Magic string 'A2R2' not present at offset 0")
        raise_if(data[4] != 0xFF, A2RHeaderError_NoFF, "Magic byte 0xFF not present at offset 4")
        raise_if(data[5:8] != b"\x0A\x0D\x0A", A2RHeaderError_NoLF, "Magic bytes 0x0A0D0A not present at offset 5")

    def __process_info(self, data):
        version = data[0]
        self.validate_info_version(to_uint8(version))
        disk_type = data[33]
        self.validate_info_disk_type(to_uint8(disk_type))
        write_protected = data[34]
        self.validate_info_write_protected(to_uint8(write_protected))
        synchronized = data[35]
        self.validate_info_synchronized(to_uint8(synchronized))
        creator = self.decode_info_creator(data[1:33])
        self.info["version"] = version # int
        self.info["disk_type"] = disk_type # int
        self.info["write_protected"] = (write_protected == 1) # boolean
        self.info["synchronized"] = (synchronized == 1) # boolean
        self.info["creator"] = creator # string

    def __process_strm(self, data):
        raise_if(data[-1] != 0xFF, A2RSTRMFormatError, "Missing phase reset at end of STRM chunk")
        i = 0
        while i < len(data) - 1:
            location = data[i]
            capture_type = data[i+1]
            data_length = from_uint32(data[i+2:i+6])
            tick_count = from_uint32(data[i+6:i+10])
            if location not in self.flux:
                self.flux[location] = []
            self.flux[location].append(
                {"capture_type": capture_type,
                 "data_length": data_length,
                 "tick_count": tick_count,
                 "data": data[i+10:i+10+data_length]}
            )
            i = i + 10 + data_length

    def __process_meta(self, metadata_as_bytes):
        metadata = self.decode_metadata(metadata_as_bytes)
        for line in metadata.split("\n"):
            if not line: continue
            columns_raw = line.split("\t")
            raise_if(len(columns_raw) != 2, A2RMETAFormatError, "Malformed metadata")
            key, value_raw = columns_raw
            raise_if(key in self.meta, A2RMETAFormatError_DuplicateKey, "Duplicate metadata key %s" % key)
            values = value_raw.split("|")
            if key == "language":
                list(map(self.validate_metadata_language, values))
            elif key == "requires_ram":
                list(map(self.validate_metadata_requires_ram, values))
            elif key == "requires_machine":
                list(map(self.validate_metadata_requires_machine, values))
            self.meta[key] = len(values) == 1 and values[0] or tuple(values)

    def to_json(self):
        j = {"a2r": {"info":self.info, "meta":self.meta}}
        return json.dumps(j, indent=2)

class A2RWriter(A2RValidator):
    def __init__(self, creator):
        self.info = collections.OrderedDict()
        self.meta = collections.OrderedDict()
        self.flux = collections.OrderedDict()

    def from_json(self, json_string):
        j = json.loads(json_string)
        root = [x for x in j.keys()].pop()
        self.meta.update(j[root]["meta"])

    def build_head(self):
        chunk = bytearray()
        chunk.extend(kA2R2) # magic bytes
        chunk.extend(b"\xFF\x0A\x0D\x0A") # more magic bytes
        return chunk

    def build_info(self):
        chunk = bytearray()
        chunk.extend(kINFO) # chunk ID
        chunk.extend(to_uint32(36)) # chunk size (constant)
        version_raw = to_uint8(self.info["version"])
        self.validate_info_version(version_raw)
        creator_raw = self.encode_info_creator(self.info["creator"])
        disk_type_raw = to_uint8(self.info["disk_type"])
        self.validate_info_disk_type(disk_type_raw)
        write_protected_raw = to_uint8(self.info["write_protected"])
        self.validate_info_write_protected(write_protected_raw)
        synchronized_raw = to_uint8(self.info["synchronized"])
        self.validate_info_synchronized(synchronized_raw)
        chunk.extend(version_raw) # version (int, probably 1)
        chunk.extend(creator_raw) # creator
        chunk.extend(disk_type_raw) # disk type (1=5.25 inch, 2=3.5 inch)
        chunk.extend(write_protected_raw) # write-protected (0=no, 1=yes)
        chunk.extend(synchronized_raw) # tracks synchronized (0=no, 1=yes)
        return chunk

    def build_strm(self):
        data_raw = bytearray()
        for location in self.flux.keys():
            for capture in self.flux[location]:
                data_raw.extend(to_uint8(location)) # track where this capture happened
                data_raw.extend(to_uint8(capture["capture_type"])) # 1 = timing, 2 = bits, 3 = xtiming
                data_raw.extend(to_uint32(len(capture["data"]))) # data length in bytes
                data_raw.extend(to_uint32(capture["tick_count"])) # estimated loop point in ticks
                data_raw.extend(capture["data"])
        data_raw.extend(b"\xFF")
        chunk = bytearray()
        chunk.extend(kSTRM) # chunk ID
        chunk.extend(to_uint32(len(data_raw))) # chunk size
        chunk.extend(data_raw) # all stream data
        return chunk

    def build_meta(self):
        if not self.meta: return b""
        meta_tmp = {}
        for key, value_raw in self.meta.items():
            if type(value_raw) == str:
                values = [value_raw]
            else:
                values = value_raw
            meta_tmp[key] = values
            list(map(self.validate_metadata_value, values))
            if key == "language":
                list(map(self.validate_metadata_language, values))
            elif key == "requires_ram":
                list(map(self.validate_metadata_requires_ram, values))
            elif key == "requires_machine":
                list(map(self.validate_metadata_requires_machine, values))
        data = b"\x0A".join(
            [k.encode("UTF-8") + \
             b"\x09" + \
             "|".join(v).encode("UTF-8") \
             for k, v in meta_tmp.items()]) + b"\x0A"
        chunk = bytearray()
        chunk.extend(kMETA) # chunk ID
        chunk.extend(to_uint32(len(data))) # chunk size
        chunk.extend(data)
        return chunk

    def write(self, stream):
        stream.write(self.build_head())
        stream.write(self.build_info())
        stream.write(self.build_strm())
        stream.write(self.build_meta())

#---------- command line interface ----------

class BaseCommand:
    def __init__(self, name):
        self.name = name

    def setup(self, subparser, description=None, epilog=None, help=".a2r disk image", formatter_class=argparse.HelpFormatter):
        self.parser = subparser.add_parser(self.name, description=description, epilog=epilog, formatter_class=formatter_class)
        self.parser.add_argument("file", help=help)
        self.parser.set_defaults(action=self)

    def __call__(self, args):
        self.a2r_image = A2RReader(args.file)

class CommandVerify(BaseCommand):
    def __init__(self):
        BaseCommand.__init__(self, "verify")

    def setup(self, subparser):
        BaseCommand.setup(self, subparser,
                          description="Verify file structure and metadata of a .a2r disk image (produces no output unless a problem is found)")

class CommandDump(BaseCommand):
    kWidth = 30

    def __init__(self):
        BaseCommand.__init__(self, "dump")

    def setup(self, subparser):
        BaseCommand.setup(self, subparser,
                          description="Print all available information and metadata in a .a2r disk image")

    def __call__(self, args):
        BaseCommand.__call__(self, args)
        self.print_flux()
        self.print_meta()
        self.print_info()

    def print_info(self):
        print("INFO:  Format version:".ljust(self.kWidth), "%d" % self.a2r_image.info["version"])
        print("INFO:  Disk type:".ljust(self.kWidth),           ("5.25-inch", "3.5-inch")[self.a2r_image.info["disk_type"]-1])
        print("INFO:  Write protected:".ljust(self.kWidth),     dNoYes[self.a2r_image.info["write_protected"]])
        print("INFO:  Track synchronized:".ljust(self.kWidth),  dNoYes[self.a2r_image.info["synchronized"]])
        print("INFO:  Creator:".ljust(self.kWidth),             self.a2r_image.info["creator"])

    def print_flux(self):
        for location in self.a2r_image.flux:
            for flux_record in self.a2r_image.flux[location]:
                print(("STRM:  Track %d%s" % (location/4, tQuarters[location%4])).ljust(self.kWidth),
                      dTiming[flux_record["capture_type"]], "capture,",
                      flux_record["tick_count"], "ticks")

    def print_meta(self):
        if not self.a2r_image.meta: return
        for key, values in self.a2r_image.meta.items():
            if type(values) == str:
                values = [values]
            print(("META:  " + key + ":").ljust(self.kWidth), values[0])
            for value in values[1:]:
                print("META:  ".ljust(self.kWidth), value)

class CommandExport(BaseCommand):
    def __init__(self):
        BaseCommand.__init__(self, "export")

    def setup(self, subparser):
        BaseCommand.setup(self, subparser,
                          description="Export (as JSON) all information and metadata from a .a2r disk image")

    def __call__(self, args):
        BaseCommand.__call__(self, args)
        print(self.a2r_image.to_json())

class WriterBaseCommand(BaseCommand):
    def __call__(self, args):
        BaseCommand.__call__(self, args)
        self.args = args
        # maintain creator if there is one, otherwise use default
        self.output = A2RWriter(self.a2r_image.info.get("creator", __displayname__))
        self.output.flux = self.a2r_image.flux.copy()
        self.output.info = self.a2r_image.info.copy()
        self.output.meta = self.a2r_image.meta.copy()
        self.update()
        tmpfile = args.file + ".chery"
        with open(tmpfile, "wb") as f:
            self.output.write(f)
        os.rename(tmpfile, args.file)

class CommandEdit(WriterBaseCommand):
    def __init__(self):
        WriterBaseCommand.__init__(self, "edit")

    def setup(self, subparser):
        WriterBaseCommand.setup(self,
                                subparser,
                                description="Edit information and metadata in a .a2r disk image",
                                epilog="""Tips:

 - Use repeated flags to edit multiple fields at once.
 - Use "key:" with no value to delete a metadata field.
 - Keys are case-sensitive.
 - Some values have format restrictions; read the .a2r specification.""",
                                help=".a2r disk image (modified in place)",
                                formatter_class=argparse.RawDescriptionHelpFormatter)
        self.parser.add_argument("-i", "--info", type=str, action="append",
                                 help="""change information field.
INFO format is "key:value".
Acceptable keys are disk_type, write_protected, synchronized, creator, version.
Other keys are ignored.
For boolean fields, use "1" or "true" or "yes" for true, "0" or "false" or "no" for false.""")
        self.parser.add_argument("-m", "--meta", type=str, action="append",
                                 help="""change metadata field.
META format is "key:value".
Standard keys are title, subtitle, publisher, developer, copyright, version, language, requires_ram,
requires_machine, notes, side, side_name, contributor, image_date. Other keys are allowed.""")

    def update(self):
        # add all new info fields
        for i in self.args.info or ():
            k, v = i.split(":", 1)
            if k in ("write_protected","synchronized"):
                v = v.lower() in ("1", "true", "yes")
            self.output.info[k] = v
        # add all new metadata fields, and delete empty ones
        for m in self.args.meta or ():
            k, v = m.split(":", 1)
            v = v.split("|")
            if len(v) == 1:
                v = v[0]
            if v:
                self.output.meta[k] = v
            elif k in self.output.meta.keys():
                del self.output.meta[k]

class CommandImport(WriterBaseCommand):
    def __init__(self):
        WriterBaseCommand.__init__(self, "import")

    def setup(self, subparser):
        WriterBaseCommand.setup(self, subparser,
                                description="Import JSON file to update metadata in a .a2r disk image")

    def update(self):
        self.output.from_json(sys.stdin.read())

if __name__ == "__main__":
    import sys
    raise_if = lambda cond, e, s="": cond and sys.exit("%s: %s" % (e.__name__, s))
    cmds = [CommandDump(), CommandVerify(), CommandEdit(), CommandExport(), CommandImport()]
    parser = argparse.ArgumentParser(prog=__progname__,
                                     description="""A multi-purpose tool for manipulating .a2r disk images.

See '""" + __progname__ + """ <command> -h' for help on individual commands.""",
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-v", "--version", action="version", version=__displayname__)
    sp = parser.add_subparsers(dest="command", help="command")
    for command in cmds:
        command.setup(sp)
    args = parser.parse_args()
    args.action(args)
