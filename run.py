# TODO: modify this file as necessary, to implement the moving average
#  and process incoming data to the appropriate destination

import sys
import os.path
import struct
import getopt
from time import time, sleep
from pathlib import Path

from model.stream import Stream_params

ROOT = Path(__file__).parent

def print_if_v(message):
    if VERBOSE_OPT:
        print(message)


def wait_for_file_to_exist(infilename: str, timeout_in_seconds: int):
    now = time()
    while not os.path.exists(infilename):
        if time() > now + timeout_in_seconds:
            raise Exception(f"Waiting for {infilename} for more than {timeout_in_seconds} seconds.") 

def create_dict_from_args(args: str):
    dic_args = {}
    for arg in args:
        win_len, infilename, outfilename = arg.split(",")
        dic_args[infilename] = (win_len, outfilename)
    return dic_args

def set_of_newly_available_pipes(available_pipes, pipelist):
    current_available_pipes = set()
    for pipe in pipelist:
        if os.path.exists(pipe) or pipe == '-':
            current_available_pipes.add(pipe)
    newly_available_pipes = current_available_pipes - available_pipes
    return newly_available_pipes
        

def process_streams(stream_params):
    def decode(buffer):
        n = len(buffer) // 8
        return [struct.unpack("<d", buffer[i * 8 : (i + 1) * 8])[0] for i in range(n)]
    
    def compute_averages(numbers):
        if len(numbers) < win_len:
            return None
        outputs_number = len(numbers) - win_len + 1
        return [sum(numbers[i : i + win_len]) / win_len for i in range(outputs_number)]
    
    for stream_param in stream_params:
        win_len = stream_param.win_len
        infile_name = stream_param.infile.name
        outfile_name = stream_param.outfile.name
        buffer = stream_param.infile.read()
        if buffer:
            numbers = decode(buffer)
            print_if_v(f"Numbers in {infile_name} : {numbers}")
            results = compute_averages(numbers)
            
            for result in results:
                stream_param.outfile.write(struct.pack("<d", result))
            print_if_v(f"\nAverages written in {outfile_name} : {results}")
            print_if_v(f"{stream_param} processed")
   

if __name__ == "__main__":
    
    time_to_process_files_in_seconds = 5
    stream_params = []
    opts, args = getopt.getopt(sys.argv[1:], "v", "verbose")
    VERBOSE_OPT = len(opts) > 0 and opts[0][0] in {'-v', '--verbose'}
    dic_args = create_dict_from_args(args)
    pipelist = dic_args.keys()
    print_if_v(f"NPipelist : {pipelist}")
    available_pipes = set()
    newly_available_pipes = set_of_newly_available_pipes(available_pipes, pipelist)
    now = time()
    while time() < now + time_to_process_files_in_seconds and available_pipes != pipelist:
        if newly_available_pipes:
            print_if_v(f"Newly available pipes : {newly_available_pipes}")
            for infilename in newly_available_pipes:
                win_len, outfilename = dic_args[infilename]
                print_if_v(f"dealing with {infilename}")
                infile = sys.stdin.buffer if infilename == "-" else open(infilename, "rb")
                outfile = sys.stdout.buffer if outfilename == "-" else open(outfilename, "wb")
                stream_param = Stream_params(int(win_len), infile, outfile)
                stream_params.append(stream_param)
                print_if_v(f"{stream_param} added.")
            available_pipes |= newly_available_pipes
            print_if_v(f"Available pipes : {available_pipes}")
        process_streams(stream_params)
        newly_available_pipes = set_of_newly_available_pipes(available_pipes, pipelist=dic_args.keys())
    print_if_v("End of listening")
