

def read(data, base, offset, stride, size, num):
    lst = []
    address = base + offset
    for i in range(num):
        b = data[address:address+size]
        lst.append(int.from_bytes(b, byteorder='little', signed=False))
        address += stride
    return lst

def write(data, lst, base, offset, stride, size):
    address = base + offset
    for i, b in enumerate(lst):
        d = b.to_bytes(size, byteorder='little', signed=False)
        data[address:address+size] = d
        address += stride
