import os
from sh import Command


class Sox:
    __sox = None

    def __init__(self) -> None:
        self.__sox = Command("sox")

    def downsample(self, infile: str, sampling_rate: int, outfile: str):
        if not infile.endswith(".wav"):
            raise FileNotFoundError
        if not os.path.exists(infile):
            raise FileNotFoundError
        self.__sox(
            infile,
            "-r {}".format(sampling_rate),
            "-c 1",
            "-b 16",
            "--endian",
            "little",
            outfile,
        )
        if not os.path.exists(outfile):
            raise FileNotFoundError


class Ffmpeg:
    __ffmpeg = None

    def __init__(self) -> None:
        self.__ffmpeg = Command("ffmpeg")

    def convert_to_wav(self, infile: str, outfile: str):
        if not os.path.exists(infile):
            raise FileNotFoundError
        self.__ffmpeg(
            "-i", infile, outfile,
        )
        if not os.path.exists(outfile):
            raise FileNotFoundError

