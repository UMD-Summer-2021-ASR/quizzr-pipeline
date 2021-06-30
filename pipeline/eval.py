from typing import Dict, List

import jiwer


def accuracy(files: List[Dict[str, str]], hypothesis_path: str) -> Dict:
    default_transformation = jiwer.Compose(
        [
            jiwer.RemoveMultipleSpaces(),
            jiwer.Strip(),
            jiwer.SentencesToListOfWords(),
            jiwer.RemoveEmptyStrings(),
        ]
    )
    hypo = open(hypothesis_path, "r").readlines()
    asr = dict()
    error = dict()
    for lines in hypo:
        [file_id, transcript] = lines.split(" ", 1)
        asr[file_id] = transcript
    for file in files:
        if file["transcript"]:
            truth = file["transcript"]
            print(truth, asr[file["_id"]])
            wer = jiwer.wer(
                truth, asr[file["_id"]], default_transformation, default_transformation
            )
            mer = jiwer.mer(
                truth, asr[file["_id"]], default_transformation, default_transformation
            )
            wil = jiwer.wil(
                truth, asr[file["_id"]], default_transformation, default_transformation
            )
            error[file["_id"]] = {"wer": wer, "mer": mer, "wil": wil}
        else:
            error[file["_id"]] = {"wer": -1, "mer": -1, "wil": -1}
    return error
