from kaldi.falign import align
import os
from pathlib import Path, PurePath

from commands.cmd import Sox
from commands import shelldon
from kaldi import diar, preprocess

default_args = {
    "batch_size": 4,
    "backend_url": "http://localhost:5000",
    "audio_path": "egs",
    "store_path": "processed_data",
    "model_directory": "models",
}


def quizzr_kaldi_pipeline():
    """
    ### Quizzr Kaldi Pipeline
    This is a simple Apache Airflow pipeline using the TaskFlow API. It fetches a batch of 
    unprocessed audio from quizzr server, downloads audio from google drive, processed the audio 
    using Kaldi (VAD,DIAR,ASR) and uploads the generated WebVTT transcripts to quizzr server.
    """

    def PreprocessData(subpath: str, mfcc_conf: str, sample_rate=8000) -> str:
        """
        #### Pre Process Audio
        A simple pre processing task which takes in the downloaded audio and
        generates files necessary for feeding into Kaldi Pipeline. It has 3 main steps:
        * Downsampling
        * Generating Data Directory Structure
        * Voice Activity Detection

        Parameters:
           subpath (str): Folder inside the  `default_arguments[store_path]` to store the processed files
           sample_rate (int) :  Sampling Rate (in Hertz) for Downsampling the Audio Files
        """
        audio_path = PurePath(default_args["audio_path"])
        store_path = PurePath(os.path.join(default_args["store_path"], subpath))
        os.makedirs(store_path.joinpath("audio"), exist_ok=True)
        for file in os.listdir(audio_path):
            if file.endswith(".wav"):
                Sox().downsample(
                    audio_path.joinpath(file),
                    sample_rate,
                    "{}/audio/{}.wav".format(store_path, Path(file).stem,),
                )
        preprocess.generate_kaldi_files(audio_path, store_path)
        preprocess.voice_activity_detection(store_path, mfcc_conf)
        return store_path

    def SpeakerDiarization(
        store_path, detect_num_speakers=False, max_num_speakers=1, threshold=0.5
    ) -> str:
        """
        #### Speaker Diarization
        Generates timestamps for different speakers using the processed audio.

        ! USE `detect_num_speakers` with caution, highly unstable.

        Parameters:
           subpath (str): Folder inside the  `default_arguments[store_path]` to store the processed files
           sample_rate (int) :  Sampling Rate (in Hertz) for Downsampling the Audio Files

        Result:
            rttm (Path): Path to the generated rttm file.
        """

        if not os.path.exists(os.path.join(store_path, "reco2num_spk")):
            with open(os.path.join(store_path, "reco2num_spk"), "w") as f:
                for file in os.listdir(os.path.join(store_path, "audio")):
                    f.write("{} {}\n".format(Path(file).stem, max_num_speakers))
        diar.diarize(store_path, detect_num_speakers, threshold)
        rttm_path = os.path.join(
            store_path, "xvectors", "plda_scores_speakers", "rttm",
        )
        if not os.path.exists(rttm_path):
            raise FileNotFoundError
        return rttm_path

    def AutomaticSpeechRecognition(store_path: str):
        shelldon.call(
            "kaldi/asr.sh {} {}".format(
                default_args["model_directory"] + "/api.ai-kaldi-asr-model",
                os.path.join(store_path, "cleaned"),
            )
        )
        return os.path.join(store_path, "cleaned", "final.ctm")

    def ForcedAlignment(ctm_path: str, rttm_path: str):
        align(ctm_path, rttm_path, default_args["store_path"] + "/vtt")

    asr_preprocessed_path = PreprocessData("asr", "asr.conf", 16000)
    diar_preprocessed_path = PreprocessData("diar", "mfcc.conf", 8000)
    ctm_path = AutomaticSpeechRecognition(asr_preprocessed_path)
    rttm_path = SpeakerDiarization(diar_preprocessed_path)
    print(ctm_path, rttm_path)
    ForcedAlignment(ctm_path, rttm_path)


quizzr_kaldi_pipeline()
