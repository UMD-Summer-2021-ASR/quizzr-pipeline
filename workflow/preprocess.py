from os import listdir, path
from pathlib import Path, PurePath

import audioread
from commands import shelldon


def generate_kaldi_files(audio_path: PurePath, store_path: PurePath):
    wav_scp = open(path.join(store_path, "wav.scp"), "w")
    segments = open(path.join(store_path, "segments"), "w")
    utt2spk = open(path.join(store_path, "utt2spk"), "w")
    for file in listdir(audio_path):
        if file.endswith(".wav"):
            wav_scp.write(
                "{}  {}\n".format(Path(file).stem, store_path.joinpath("audio", file))
            )
            utt2spk.write("{0}_001 {0}\n".format(Path(file).stem))
            segments.write(
                "{0}_001 {0} 0.0 {1}\n".format(
                    Path(file).stem,
                    audioread.audio_open(audio_path.joinpath(file)).duration,
                )
            )
    wav_scp.close()
    segments.close()
    utt2spk.close()


def voice_activity_detection(store_path: PurePath, mfcc_conf: str):
    shelldon.call("utils/fix_data_dir.sh {}".format(store_path))
    shelldon.call(
        "steps/make_mfcc.sh --nj 1 --mfcc-config conf/{0} {1} {1}/make_mfcc {1}/mfcc".format(
            mfcc_conf, store_path
        )
    )
    shelldon.call("steps/compute_vad_decision.sh {0} {0}/vad".format(store_path))
    shelldon.call("diarization/vad_to_segments.sh {0} {0}/cleaned".format(store_path))

