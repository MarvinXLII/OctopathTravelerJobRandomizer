

def spurningRibbon(uasset, uexp):
    
    # Replace Soothing Seed with Spurning Ribbon
    uasset[0x11e8:0x11f2] = bytearray([0x49, 0x54, 0x4d, 0x5f, 0x41, 0x43, 0x5f, 0x30, 0x34, 0x31])
    uasset[0x11f3:0x11f8] = bytearray([0xaa, 0xf, 0x46, 0xa6, 0x0b])

    # Give to each CP
    item = 0x683
    count = 0x6ec
    stride = 0x765
    for i in range(8):
        uexp[item] = 0x81
        uexp[count] = 1
        item += stride
        count += stride

def inits(path, settings):

    with open(f"{path}/PlayableCharacterDB.uasset", 'rb') as file:
        uasset = bytearray(file.read())
    with open(f"{path}/PlayableCharacterDB.uexp", 'rb') as file:
        uexp = bytearray(file.read())

    if settings['spurning-ribbon']:
        spurningRibbon(uasset, uexp)

    with open(f"{path}/PlayableCharacterDB.uasset", 'wb') as file:
        file.write(uasset)
    with open(f"{path}/PlayableCharacterDB.uexp", 'wb') as file:
        file.write(uexp)
