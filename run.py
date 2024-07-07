# TODO: modify this file as necessary, to implement the moving average
#  and process incoming data to the appropriate destination

import sys
import os.path
import struct
import getopt
from time import time
from pathlib import Path
from typing import Union, Any

from model.stream import Stream_params

ROOT = Path(__file__).parent

def print_if_v(message: str):
    """prints if the -v option has been put"""
    if VERBOSE_OPT:
        print(message)


def get_seconds_to_listen(opts):
    """returns from the options the number of seconds the process will listen to the pipes"""
    
    seconds_to_listen = int([opt[1] for opt in opts if opt[0] in {'-t', '--time'}][0])
    print_if_v(f"The reading will occur for {seconds_to_listen} seconds.")
    return seconds_to_listen

def create_dict_from_args(args: str) -> dict[str, tuple[str, str]]:
    """creates a dictionary where the keys are the infile and the values are a tuple of win_len and outfile"""
    dic_args = {}
    for arg in args:
        win_len, infilename, outfilename = arg.split(",")
        dic_args[infilename] = (win_len, outfilename)
    return dic_args


def get_pipes_to_read(dic_args):
    """gets the set of the pipes to read from the options
    Args:
        dic_args (dict): the dictionary built from the args
    Returns:
        set: the set of pipes
    """
    pipes_set = set(dic_args.keys())
    print_if_v(f"Set of pipes expected : {pipes_set}")
    return pipes_set

def get_newly_available_pipes_set(pipes_to_check: set[str]) -> set[str]:
    """
    gets the set of pipes that are now available
    @param available_pipes : the set of the pipes already availables
    @param pipeset : the set of all the pipes expeceted to be used
    @return : the set of newly available pipes
    """
    newly_available_pipes = {pipe for pipe in pipes_to_check if os.path.exists(pipe) or pipe == '-'}
    if newly_available_pipes:
        print_if_v(f"Newly available pipes : {newly_available_pipes}")
    return newly_available_pipes
        
def add_stream_param(infilename: str) -> None:
    """
    update the list stream_params with the stream given by the infilename 
    """
    win_len, outfilename = dic_args[infilename]
    print_if_v(f"Dealing with {infilename}")
    infile = sys.stdin.buffer if infilename == "-" else open(infilename, "rb")
    outfile = sys.stdout.buffer if outfilename == "-" else open(outfilename, "wb")
    stream_param = Stream_params(int(win_len), infile, outfile)
    stream_params.append(stream_param)
    print_if_v(f"{stream_param} added.")


def process_streams(stream_params: Stream_params):
    def decode(buffer: bytes) -> list[float]:
        """
        reads the binary data from the buffer and returns the list of corresponding numbers
        Args:
            buffer : the binary data
        Returns:
            list[float]: the numbers read
        """
        n = len(buffer) // 8
        numbers = [struct.unpack("<d", buffer[i * 8 : (i + 1) * 8])[0] for i in range(n)]
        print_if_v(f"Numbers in {infile_name} : {numbers}")
        return numbers
    
    def compute_averages(numbers: list[float]) -> Union[None, list[float]]:
        """Computes the moving averages list given the ones in numbers, if the list doesn't have enough numbers, it returns None.
        Args:
            numbers (list[float]): the numbers to compute averages
        Returns:
            Union[None, list[float]]: the list of averages
        """
        if len(numbers) < win_len:
            return None
        outputs_number = len(numbers) - win_len + 1
        return [sum(numbers[i : i + win_len]) / win_len for i in range(outputs_number)]
    
    def write_averages_in_file(results, outfile):
        for result in results:
            outfile.write(struct.pack("<d", result))
        print_if_v(f"\nAverages written in {outfile_name} : {results}")
        
    for stream_param in stream_params:
        win_len, infile_name, outfile_name = stream_param.win_len, stream_param.infile.name, stream_param.outfile.name
        buffer = stream_param.infile.read()
        if buffer:
            numbers = decode(buffer)
            results = compute_averages(numbers)
            write_averages_in_file(results, stream_param.outfile)
        print_if_v(f"{stream_param} processed")
   

if __name__ == "__main__":
    
    opts, args = getopt.getopt(sys.argv[1:], "vt:", ["verbose", "time ="])
    opts_name = {opt[0] for opt in opts}
    VERBOSE_OPT = len(opts_name.intersection({'-v', '--verbose'})) > 0
    WITH_TIME = len(opts_name.intersection({'-t', '--time'})) > 0
    
    if WITH_TIME:
        seconds_to_listen = get_seconds_to_listen(opts)
    
    dic_args = create_dict_from_args(args)
    pipes_set = get_pipes_to_read(dic_args)
    
    stream_params = []
    newly_available_pipes = get_newly_available_pipes_set(pipes_set)
    start = time()
    
    while (WITH_TIME and time() < start + seconds_to_listen) or (not WITH_TIME and len(pipes_set) > 0):
        if newly_available_pipes:
            for infilename in newly_available_pipes:
                add_stream_param(infilename)
            pipes_set -= newly_available_pipes
            print_if_v(f"Pipes left to check : {pipes_set}")
        process_streams(stream_params)
        newly_available_pipes = get_newly_available_pipes_set(pipes_set)
    
    if WITH_TIME and time() > start + seconds_to_listen and len(pipes_set) > 0:
        raise Exception(f"The pipes {','.join([pipe for pipe in pipes_set])} are not present after {seconds_to_listen} seconds.")
    print_if_v("End of listening")
