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
    
    opts, args = getopt.getopt(sys.argv[1:], "vt:", ["verbose", "time ="])
    opts_name = {opt[0] for opt in opts}
    VERBOSE_OPT = len(opts_name.intersection({'-v', '--verbose'})) > 0
    WITH_TIME = len(opts_name.intersection({'-t', '--time'})) > 0
    print_if_v(WITH_TIME)
    if WITH_TIME:
        time_to_read_in_seconds = int([opt[1] for opt in opts if opt[0] in {'-t', '--time'}][0])
        print_if_v(time_to_read_in_seconds)
    dic_args = create_dict_from_args(args)
    pipeset = set(dic_args.keys())
    print_if_v(f"Pipeset : {pipeset}")
    
    stream_params = []
    available_pipes = set()
    newly_available_pipes = set_of_newly_available_pipes(available_pipes, pipeset)
    print_if_v(f"Newly_available pipes : {newly_available_pipes}")
    start = time()
    while (WITH_TIME and time() < start + time_to_read_in_seconds) or (not WITH_TIME and available_pipes != pipeset):
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
        newly_available_pipes = set_of_newly_available_pipes(available_pipes, pipeset)
    
    if WITH_TIME and time() > start + time_to_read_in_seconds and available_pipes != pipeset:
        raise Exception(f"The pipes {','.join([pipe for pipe in pipeset - available_pipes])} are not present after {time_to_read_in_seconds} seconds.")
    print_if_v("End of listening")
