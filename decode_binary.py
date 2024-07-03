import struct

def decode(buffer):
    return [struct.unpack("<d", buffer[i * 8 : (i + 1) * 8])[0] for i in range(5)]

if __name__ == "__main__":
    infile = open("output", "rb")
    processed = decode(infile.read())
    print(processed)
    with open('out.txt', 'w') as f:
        for i in processed:
            f.write(str(i))
