# TODO: modify this file as necessary, to implement the moving average
#  and process incoming data to the appropriate destination

import sys
import os.path
import struct
import getopt
from time import time
from pathlib import Path

ROOT = Path(__file__).parent
V_option = False

def print_if_v(message):
    if VERBOSE_OPT:
        print(message)

# streams is a list of tuples (window_length, input_file, output_file)
def process_streams(streams):
    def decode(buffer):
        n = len(buffer) // 8
        return [struct.unpack("<d", buffer[i * 8 : (i + 1) * 8])[0] for i in range(n)]
    
    def compute_averages(numbers):
        if len(numbers) < win_len:
            return None
        outputs_number = len(numbers) - win_len + 1
        return [sum(numbers[i : i + win_len]) / win_len for i in range(outputs_number)]
    print_if_v("processing")
    for stream in streams:
        win_len, input_file, output_file = stream
        if os.path.exists(ROOT / output_file.name):
            os.remove(ROOT / output_file.name)

        numbers = decode(input_file.read())
        print_if_v(numbers)
        results = compute_averages(numbers)
        print_if_v(results)
        for result in results:
            output_file.write(struct.pack("<d", result))
        print_if_v(f"stream {stream} processed")
   

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
        stream_param = (int(win_len), infile, outfile)
        stream_params.append(stream_param)
        print_if_v(f"stream_param {stream_param} added.")
    process_streams(stream_params)
