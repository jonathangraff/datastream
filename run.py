import sys
import os.path
import struct
from getopt import getopt
from time import time
from pathlib import Path
from typing import Union
from io import BufferedWriter

from model.stream import Stream_params

ROOT = Path(__file__).parent

def print_if_v(message: str) -> None:
    """prints the message if the -v option has been put
    Args:
        message (str): the message to display
    Returns:
        None"""
    if VERBOSE_OPT:
        print(message)


def get_seconds_to_listen(opts: list[tuple[str, str]]) -> int:
    """returns from the options the number of seconds the process will listen to the pipes
    Args:
        opts (list[tuple[str, str]]): the options passed to the terminal
    Returns:
        seconds_to_listen: int"""
    
    seconds_to_listen = int([opt[1] for opt in opts if opt[0] in {'-t', '--time'}][0])
    print_if_v(f"The reading will occur for {seconds_to_listen} seconds.")
    return seconds_to_listen


def create_dict_from_args(args: list[str]) -> dict[str, tuple[str, str]]:
    """creates a dictionary where the keys are the infile and the values are a tuple of win_len and outfile
    Args:
        args (list[str]): the arguments passed to the terminal
    Returns:
        dic_args (dict[str, tuple[str, str]): the dictionary"""
    dic_args = {}
    for arg in args:
        win_len, infilename, outfilename = arg.split(",")
        dic_args[infilename] = (win_len, outfilename)
    return dic_args


def get_pipes_to_read(dic_args: dict[str, tuple[str, str]]) -> set[str]:
    """gets the set of the pipes to read from the arguments
    Args:
        dic_args (dict[str, tuple[str, str]]): the dictionary built from the args
    Returns:
        pipes_set (set[str]): the set of pipes to read
    """
    pipes_set = set(dic_args.keys())
    print_if_v(f"Set of pipes expected : {pipes_set}")
    return pipes_set

def get_newly_available_pipes_set(pipes_to_check: set[str]) -> set[str]:
    """gets the set of pipes that are now available to process
    Args:
        pipes_to_check set[str]: the set of the pipes to check
    Returns: 
        newly_available_pipes (set[str]): the set of newly available pipes amongst the ones passed in argument
    """
    newly_available_pipes = {pipe for pipe in pipes_to_check if os.path.exists(pipe) or pipe == '-'}
    if newly_available_pipes:
        print_if_v(f"Newly available pipes : {newly_available_pipes}")
    return newly_available_pipes
        
def add_stream_param(infilename: str) -> None:
    """
    update the list stream_params with the stream given by the infilename 
    Args:
        infilename (str): the name of the infile
    Returns:
        None
    """
    win_len, outfilename = dic_args[infilename]
    print_if_v(f"Dealing with {infilename}")
    infile = sys.stdin.buffer if infilename == "-" else open(infilename, "rb")
    outfile = sys.stdout.buffer if outfilename == "-" else open(outfilename, "wb")
    stream_param = Stream_params(int(win_len), infile, outfile)
    stream_params.append(stream_param)
    print_if_v(f"{stream_param} added.")


def process_streams(stream_params: Stream_params) -> None:
    """Processes the stream passed in parameter
    Args:
        stream_params (Stream_params): the list of streams to process
    Returns:
        None
    """
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
    
    def write_averages_in_file(averages: list[int], outfile: BufferedWriter) -> None:
        """Writes the moving averages in a file or on the standard output.
        Args:
            averages (list[int]): the averages to write in the file
            outfile (BufferedWriter): the file where to write the averages
        Returns:
            None
        """
        for average in averages:
            outfile.write(struct.pack("<d", average))
        print_if_v(f"\nAverages written in {outfile_name} : {averages}")
        
    for stream_param in stream_params:
        win_len, infile_name, outfile_name = stream_param.win_len, stream_param.infile.name, stream_param.outfile.name
        buffer = stream_param.infile.read()
        if buffer:
            numbers = decode(buffer)
            results = compute_averages(numbers)
            write_averages_in_file(results, stream_param.outfile)
        print_if_v(f"{stream_param} processed")
   

if __name__ == "__main__":
    
    opts, args = getopt(sys.argv[1:], "vt:", ["verbose", "time ="])
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
