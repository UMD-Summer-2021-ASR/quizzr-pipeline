import os
from typing import List, Dict, Set
from decimal import Decimal


def align(ctm: str, rttm: str, vtt: str):
    os.makedirs(vtt, exist_ok=True)
    with open(ctm, "r") as ctm:
        ctm = ctm.readlines()
    with open(rttm, "r") as rt:
        rttm = rt.readlines()
        process(ctm=ctm, rttm=rttm, dir=vtt)


def process(ctm: List[str], rttm: List[str], dir):
    speaker: Dict[str, Dict[str, List]] = dict()
    files: Set[str] = set()
    for l in rttm:
        [_, file, _, start, dur, _, _, id, _, _] = l.split()
        files.add(file)
        speaker.setdefault(file, {"rttm": [], "sub": []})
        speaker[file]["rttm"].append([id, start, dur])
    for l in ctm:
        [file, _, start, dur, word] = l.split()
        speaker[file]["sub"].append([word, start, dur])
    for file in files:
        with open(dir + "/" + file + ".vtt", "w") as f:
            f.write("WEBVTT Kind: captions; Language: en\n\n")
            for line in speaker[file]["sub"]:
                spk = 1
                for sp in speaker[file]["rttm"]:
                    if float(sp[1]) <= float(line[1]):
                        spk = sp[0]
                f.write(
                    "00:{} --> 00:{}\n<v Speaker {}>{}\n\n".format(
                        line[1], Decimal(line[1]) + Decimal(line[2]), spk, line[0]
                    )
                )

