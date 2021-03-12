import os
import hashlib
import sys
import zlib

class ROM:
    def __init__(self, fileName, patches=None):
        self.file = open(fileName, 'rb')

        # Load pointers to files
        self.file.seek(-44, 2)
        self.unknown = self.readInt(8) # Something from the original Pak; remains constant in patches
        self.fileSectionStart = self.readInt(8)
        self.fileSectionSize = self.readInt(8)
        self.fileSectionSHA1 = self.readBytes(20)
        assert self.checkSHA(self.fileSectionStart, self.fileSectionSize, self.fileSectionSHA1)

        # Setup for reading entries
        self.file.seek(self.fileSectionStart)
        size = self.readInt(4)
        self.baseDir = self.readString(size)
        self.file.seek(4, 1) # Number of files (== len(self.files))

        # Read entries
        self.files = {}
        while self.file.tell() < self.fileSectionStart + self.fileSectionSize:
            self.readFileEntry()

        # For extracted files
        self.data = {}
        self.isPatched = {}

        # Patches
        if patches:
            self.patches = [ROM(patch) for patch in patches]
        else:
            self.patches = []

    def clean(self):
        self.data = {}
        self.isPatched = {}
        for patch in self.patches:
            patch.clean()

    def patchFile(self, data, fileName):
        key = self.getFullPath(fileName)
        if self.data[key] != data:
            self.data[key] = data
            self.isPatched[key] = True

    def getFullPath(self, fileName):
        for key in self.files:
            if key == fileName:
                return key
            if os.path.basename(key) == fileName:
                return key
            if fileName in key:
                return key
                    
    def extractFile(self, fileName):
        key = self.getFullPath(fileName)
        if not key: return

        # Check most recent patches first!
        data = None
        for patch in self.patches:
            if key in patch.files:
                data = patch.extractFile(fileName)
                break

        if not data:
            f = self.files[key]
            if f['isComp']:
                pointers = f['pointers']
                data = bytearray([])
                for start, end in pointers:
                    self.file.seek(start)
                    size = end - start
                    tmp = self.readBytes(size)
                    data += zlib.decompress(tmp)
            else:
                pointer = f['base'] + 8*3 + 4 + 20 + 5
                self.file.seek(pointer)
                data = self.readBytes(f['size'])

        
        self.data[key] = data
        self.isPatched[key] = False
        return self.data[key]

    def compressFile(self, data):
        base = 0
        size = 0x10000
        comp = bytearray([])
        pointers = []
        while base < len(data):
            start = len(comp)
            comp += zlib.compress(data[base:base+size])
            base += size
            end = len(comp)
            pointers.append((start, end))
        return comp, pointers
        
    def readFileEntry(self):
        size = self.readInt(4)
        fileName = self.readString(size)
        assert fileName not in self.files
        f = {}
        f['base'] = self.readInt(8)
        f['size'] = self.readInt(8)
        f['decompSize'] = self.readInt(8)
        f['isComp'] = self.readInt(4)
        f['sha1'] = self.readBytes(20) # compressed data
        f['count'] = self.readInt(4)
        f['pointers'] = []
        if f['isComp']:
            for _ in range(f['count']):
                f['pointers'].append([
                    self.readInt(8), # base
                    self.readInt(8), # end
                    # end - base == size
                ])
            self.file.seek(5, 1)
        else: # File is not compressed
            assert f['count'] == 0
            self.file.seek(1, 1)
            f['pointers'].append([
                f['base'] + 8*3+4+20+5,
                f['base'] + 8*3+4+20+5 + f['size'],
            ])
        # Store entry
        self.files[fileName] = f

        address = self.file.tell()
        assert self.checkSHA(f['pointers'][0][0], f['size'], f['sha1'])
        self.file.seek(address)

    def readString(self, size):
        if size < 0:
            s = self.readBytes(-size*2)
            string = s.decode('utf-16')
        else:
            s = self.readBytes(size)
            string = s.decode('utf-8')
        return string[:-1]

    def pakString(self, string):
        try:
            return string.encode('utf-8') + bytearray([0])
        except:
            return string.encode('utf-16')[2:] + bytearray([0]*2)

    def readInt(self, size):
        return int.from_bytes(self.file.read(size), byteorder='little', signed=True)

    def pakInt(self, value, size=4):
        return value.to_bytes(size, byteorder='little', signed=True)
    
    def readBytes(self, size):
        return self.file.read(size)

    def checkSHA(self, base, size, sha1):
        self.file.seek(base)
        data = self.readBytes(size)
        digest = hashlib.sha1(data).digest()
        return digest == sha1

    def getSHA(self, data):
        return hashlib.sha1(data).digest()

    # PATCHED FILES ONLY
    def getBaseDir(self):
        fileNames = list(filter(lambda key: self.isPatched[key], self.data.keys()))
        comDir = os.path.dirname(os.path.commonprefix(fileNames))
        return os.path.join(self.baseDir, comDir + os.path.sep), comDir
    
    def buildPak(self, output):
        pakFile = bytearray([]) # This points to pakData entries
        pakData = bytearray([]) # This will in include comp/decomp data
        baseDir, comDir = self.getBaseDir() ## EXTREMELY IMPORTANT!!!!! BE AS SPECIFIC AS POSSIBLE TO SPEED UP PATCHING!!!
        baseDirBytes = self.pakString(baseDir)
        size = len(baseDirBytes)
        pakFile += self.pakInt(size)
        pakFile += baseDirBytes
        # Number of files
        pakFile += self.pakInt(len(self.data))
        # Loop over files
        for key, data in self.data.items():
            # Only include modified files
            if not self.isPatched[key]:
                continue
            base = len(pakData)
            # Filename (relative to the new base directory)
            tmpDir = os.path.relpath(key, comDir)
            fileName = self.pakString(tmpDir)
            size = len(fileName)
            pakFile += self.pakInt(size)
            pakFile += fileName
            # Compress
            if self.files[key]['isComp']:
                # Pointers
                pakFile += self.pakInt(base, size=8)
                pakData += self.pakInt(0, size=8)
                # Compress data
                comp, offsets = self.compressFile(data)
                # Compressed size
                pakFile += self.pakInt(len(comp), size=8)
                pakData += self.pakInt(len(comp), size=8)
                # Decompressed size
                pakFile += self.pakInt(len(data), size=8)
                pakData += self.pakInt(len(data), size=8)
                # Is compressed?
                pakFile += self.pakInt(1)
                pakData += self.pakInt(1)
                # SHA1 of (compressed) data
                pakFile += self.getSHA(comp)
                pakData += self.getSHA(comp)
                # Number of zipped segments
                pakFile += self.pakInt(len(offsets))
                pakData += self.pakInt(len(offsets))
                # Pointers to zipped segments
                pointer = base + 0x34 + 8*2*len(offsets) + 5
                for start, end in offsets:
                    # Start of entry
                    pakFile += self.pakInt(pointer + start, size=8)
                    pakData += self.pakInt(pointer + start, size=8)
                    # End of entry (==start of next entry!)
                    pakFile += self.pakInt(pointer + end, size=8)
                    pakData += self.pakInt(pointer + end, size=8)
                # Max size of decompressed entry
                pakFile += self.pakInt(0, size=1)
                pakData += self.pakInt(0, size=1)
                if len(offsets) == 1:
                    pakFile += self.pakInt(len(data))
                    pakData += self.pakInt(len(data))
                else:
                    pakFile += self.pakInt(0x10000)
                    pakData += self.pakInt(0x10000)
                pakData += comp
            else:
                # Pointers
                pakFile += self.pakInt(base, size=8)
                pakData += self.pakInt(0, size=8)
                # Entry size
                pakFile += self.pakInt(len(data), size=8)
                pakData += self.pakInt(len(data), size=8)
                # Decompressed size
                pakFile += self.pakInt(len(data), size=8)
                pakData += self.pakInt(len(data), size=8)
                # Is compressed?
                pakFile += self.pakInt(0)
                pakData += self.pakInt(0)
                # SHA1 of (compressed) data
                pakFile += self.getSHA(data)
                pakData += self.getSHA(data)
                # Number of zips
                pakFile += self.pakInt(0, size=5)
                pakData += self.pakInt(0, size=5)
        # FINISH PAK FILE
        sha = self.getSHA(pakFile)
        fileSize = len(pakFile)
        pakFile += self.pakInt(0, size=1)
        pakFile += self.pakInt(self.unknown, size=8)
        pakFile += self.pakInt(len(pakData), size=8)
        pakFile += self.pakInt(fileSize, size=8)
        pakFile += sha
        # Build Pak
        pak = pakData + pakFile
        with open(output, 'wb') as file:
            file.write(pak)


if __name__ == '__main__':
    pak = sys.argv[1]
    base = os.path.splitext(pak)[0]

    if os.path.isdir(base):
        print(f"Directory exists. Must manually remove the directory to unpak {pak}")
        sys.exit()

    # Extract all files of the pak and dump
    rom = ROM(pak)
    for file in rom.files:
        data = rom.extractFile(file)
        fileName = os.path.join(base, file)
        dirName = os.path.dirname(fileName)
        if not os.path.isdir(dirName):
            os.makedirs(dirName)
        with open(fileName, 'wb') as f:
            f.write(data)
