# TODO: modify this file as necessary, to implement the moving average
#  and process incoming data to the appropriate destination

import sys
import os.path
import shlex
import struct
import subprocess
from time import sleep
from pathlib import Path

ROOT = Path(__file__).parent

# streams is a list of tuples (window_length, input_file, output_file)
def process_streams(streams):
    def decode(buffer):
        i = 0
        numbers = []
        while True:
            try:
                buffer8 = buffer[i : i + 8]
                to_add = struct.unpack("<d", buffer8)[0]
                numbers.append(to_add)
                i += 8
            except struct.error:
                break
        return numbers
    
    def compute_averages(numbers, win_len):
        if len(numbers) < win_len:
            return None
        outputs_number = len(numbers) - win_len + 1
        return [sum(numbers[i : i + win_len]) / win_len for i in range(outputs_number)]

    for stream in streams:
        win_len, input_file, output_file = stream
        if os.path.exists(ROOT / output_file.name):
            os.remove(ROOT / output_file.name)

        numbers = decode(input_file.read())
        print(numbers)
        input_file.close()
        results = compute_averages(numbers, win_len)
        print(results)
        for result in results:
            output_file.write(bytearray(struct.pack("f", result)) )
        output_file.close()

        

if __name__ == "__main__":
    stream_params = []
    sleep(0.01)  # TODO: a bit hacky, wait a bit for the first stream to be available
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
