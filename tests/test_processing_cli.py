import filecmp
import glob
import os
import shlex
import subprocess
import unittest
from pathlib import Path
from shutil import which
from typing import Union

StrOrPath = Union[str, Path]
ROOT_DIR = Path(__file__).parents[1]
DATA_DIR = ROOT_DIR / "data"

# files
TMP_PIPE = DATA_DIR / "test-data"
IN_DATA = DATA_DIR / "sample-data-in"
OUT_DATA = DATA_DIR / "test-data-out"
REF_OUT_DATA = DATA_DIR / "sample-data-out"


# commands


def pick_python() -> str:
    """Return the python cmd that can be found in PATH"""
    for cmd in ("python", "python3"):
        if which(cmd):
            return cmd

    raise RuntimeError("python not found")


DATASTREAM = ROOT_DIR / "datastream.sh"
PROCESS = f"{pick_python()} {ROOT_DIR / 'processing/run.py'}"


def datastream(*streams: Union[StrOrPath, tuple[int, StrOrPath]], parallel=False):
    """Get the command to start outputting data to one or multiple streams"""

    def _get_arg(stream):
        if isinstance(stream, tuple):
            n, out = stream
        else:
            n, out = 1, stream
        return f"{IN_DATA},{out},{n}"

    return (
        f'{ROOT_DIR / "datastream.sh"}{" -p" if parallel else ""}'
        f' {" ".join([_get_arg(s) for s in streams])}'
    )


def _arg(stream_id: Union[int, str] = "", window_size=3):
    """Argument to the process CLI for a single stream"""
    return f"{window_size},{TMP_PIPE}{stream_id},{OUT_DATA}{stream_id}"


def _cleanup_files():
    # clean up tmp files
    for base_f in (TMP_PIPE, OUT_DATA):
        for f in glob.glob(f"{base_f}*"):
            os.remove(f)


# tests


class _BaseTestClass(unittest.TestCase):
    def setUp(self):
        _cleanup_files()

    def tearDown(self):
        _cleanup_files()


class BasicTests(_BaseTestClass):
    def test_named_pipes(self):
        process = subprocess.Popen(shlex.split(datastream(TMP_PIPE)))
        subprocess.run(
            shlex.split(f"{PROCESS} {_arg()}"),
            check=True,
        )
        self.assertEqual(process.poll(), 0)
        self.assertTrue(filecmp.cmp(OUT_DATA, REF_OUT_DATA, shallow=False))

    def test_stdout_stdin(self):
        process = subprocess.run(
            shlex.split(datastream("-")), stdout=subprocess.PIPE, check=True
        )
        with open(OUT_DATA, "w") as f:
            subprocess.run(
                shlex.split(f"{PROCESS} 3,-,-"),
                input=process.stdout,
                stdout=f,
                check=True,
            )

        self.assertTrue(filecmp.cmp(OUT_DATA, REF_OUT_DATA, shallow=False))


class AdvancedTests(_BaseTestClass):
    def test_multiple_right_order(self):
        process = subprocess.Popen(
            shlex.split(datastream(f"{TMP_PIPE}1", f"{TMP_PIPE}2"))
        )
        subprocess.run(
            shlex.split(f"{PROCESS} {_arg(1)} {_arg(2)}"),
            check=True,
        )
        self.assertEqual(process.poll(), 0)
        for i in (1, 2):
            self.assertTrue(filecmp.cmp(f"{OUT_DATA}{i}", REF_OUT_DATA, shallow=False))

    def test_multiple_invert_order(self):
        process = subprocess.Popen(
            shlex.split(datastream(f"{TMP_PIPE}1", f"{TMP_PIPE}2"))
        )
        subprocess.run(
            shlex.split(f"{PROCESS} {_arg(2)} {_arg(1)}"),
            check=True,
        )
        self.assertEqual(process.poll(), 0)
        for i in (1, 2):
            self.assertTrue(filecmp.cmp(f"{OUT_DATA}{i}", REF_OUT_DATA, shallow=False))

    def test_multiple_parallel(self):
        process = subprocess.Popen(
            shlex.split(datastream(f"{TMP_PIPE}1", f"{TMP_PIPE}2", parallel=True))
        )
        subprocess.run(
            shlex.split(f"{PROCESS} {_arg(2)} {_arg(1)}"),
            check=True,
        )
        self.assertEqual(process.poll(), 0)
        for i in (1, 2):
            self.assertTrue(filecmp.cmp(f"{OUT_DATA}{i}", REF_OUT_DATA, shallow=False))
