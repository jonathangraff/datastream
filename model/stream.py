class Stream_params:
    
    def __init__(self, win_len: int, infile, outfile):
        
        self.win_len = win_len
        self.infile = infile
        self.outfile = outfile
        
    def __repr__(self):
        return f"Stream with window length {self.win_len}, infile {self.infile.name} and outfile {self.outfile.name}"
    