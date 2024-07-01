**Solution so far**

* it works for shell pipe '|' and for pipe file but not tested with unitest.
* the average calculation might be calculated directly using binary
* refactoring and docstring
* additional tests
* avoid sleep

**To display the binary file numbers content on the shell:**
* single precision (32 bit)
 
  `cat out | od -An -t f4`
  
* double precision (64 bit)
  
  `cat out | od -An -t f8`

**run with pipe:**

* in one shell run:
  
  `./datastream.sh  ../helloworld/sample-data-in,pipe`

* in the other run:
 
  `python processing/run.py 3,pipe,out`
  
**run with | (stdin | stdout):**

  `cat ../helloworld/sample-data-in | python processing/run.py 3,-,-`

**run.py**

```
# TODO: modify this file as necessary, to implement the moving average
#  and process incoming data to the appropriate destination

import struct
import sys
import os
from time import sleep
from collections import deque

def decode(buffer):
    n = len(buffer)//8
    return [struct.unpack("<d", buffer[i * 8 : (i + 1) * 8])[0] for i in range(n)]

# streams is a list of tuples (window_length, input_file, output_file)
def process_streams(streams):
    chunk_size = 8
    for stream in streams:
        print( 'start stream')
        (window_length, input_file, output_file) = stream
        data_in = input_file.read(chunk_size)
        window = deque([])
        while len(data_in) == 8:
            print('data in from stream',decode(data_in), len(data_in))
            # process average
            number= decode(data_in)[0]
            if len(window) < window_length:
                window.append(number)
            else:
                avg = sum(window)/window_length
                window.popleft()
                window.append(number)
                print('----------', avg)
                float_bytes = struct.pack('d', avg)
                output_file.write(float_bytes)
            data_in = input_file.read(chunk_size)

if __name__ == "__main__":
    stream_params = []
    print('--------------')
    sleep(1)  # TODO: a bit hacky, wait a bit for the first stream to be available
    for arg in sys.argv[1:]:
        win_len, infilename, outfilename = arg.split(",")
        if infilename == "-":
            infile = sys.stdin.buffer
        else:
            infile = open(infilename, "rb")
        if outfilename == "-":
            outfile = sys.stdout.buffer
        else:
            outfile = open(outfilename, "wb")
        stream_params.append((int(win_len), infile, outfile))
    process_streams(stream_params)
```
