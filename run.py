# TODO: modify this file as necessary, to implement the moving average
#  and process incoming data to the appropriate destination

import sys
import os.path
import struct
import getopt
from time import time
from pathlib import Path

from model.stream import Stream_params

ROOT = Path(__file__).parent

def print_if_v(message):
    if VERBOSE_OPT:
        print(message)


def process_streams(stream_params):
    def decode(buffer):
        n = len(buffer) // 8
        return [struct.unpack("<d", buffer[i * 8 : (i + 1) * 8])[0] for i in range(n)]
    
    def compute_averages(numbers):
        if len(numbers) < win_len:
            return None
        outputs_number = len(numbers) - win_len + 1
        return [sum(numbers[i : i + win_len]) / win_len for i in range(outputs_number)]
    print_if_v("Processing streams...")
    
    for stream_param in stream_params:
        win_len = stream_param.win_len
        infile_name = stream_param.infile.name
        outfile_name = stream_param.outfile.name
        if os.path.exists(ROOT / outfile_name):
            os.remove(ROOT / outfile_name)

        numbers = decode(stream_param.infile.read())
        print_if_v(f"Numbers in {infile_name} : {numbers}")
        results = compute_averages(numbers)
        
        for result in results:
            stream_param.outfile.write(struct.pack("<d", result))
        print_if_v(f"\nAverages written in {outfile_name} : {results}")
        print_if_v(f"{stream_param} processed")
   

if __name__ == "__main__":
    timeout_in_seconds = 10
    stream_params = []
    opts, args = getopt.getopt(sys.argv[1:], "v", "verbose")
    VERBOSE_OPT = len(opts) > 0 and opts[0][0] in {'-v', '--verbose'}
    for arg in args:
        win_len, infilename, outfilename = arg.split(",")
        if infilename == "-":
            infile = sys.stdin.buffer
        else:
            now = time()
            while not os.path.exists(infilename):
                if time() > now + timeout_in_seconds:
                    raise Exception(f"Waiting for {infilename} for more than {timeout_in_seconds} seconds.") 
            infile = open(infilename, "rb")
        if outfilename == "-":
            outfile = sys.stdout.buffer
        else:
            outfile = open(outfilename, "wb")
        stream_param = Stream_params(int(win_len), infile, outfile)
        stream_params.append(stream_param)
        print_if_v(f"{stream_param} added.")
    process_streams(stream_params)
