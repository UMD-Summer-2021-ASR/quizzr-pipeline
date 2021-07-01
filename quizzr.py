import os
import shutil
from datetime import datetime
from pathlib import Path, PurePath
from typing import Dict, List

import requests
from airflow.decorators import dag, task
from airflow.utils.dates import days_ago

from commands import shelldon
from commands.cmd import Sox
from pipeline import diar, drive, eval, preprocess
from pipeline.falign import align

default_args = {
    "batch_size": 32,
    "backend_url": "http://localhost:3000",
    "audio_path": "data",
    "store_path": "processed_data",
    "model_directory": "models",
}


@dag(
    default_args=default_args,
    schedule_interval="*/30 * * * *",
    start_date=days_ago(1),
    tags=["kaldi"],
)
def quizzr_kaldi_pipeline():
    """
    ### Quizzr Kaldi Pipeline
    This is a simple Apache Airflow pipeline using the TaskFlow API. It fetches a batch of
    unprocessed audio from quizzr server, downloads audio from google drive, processed the audio
    using Kaldi (VAD,DIAR,ASR) and uploads the generated WebVTT transcripts to quizzr server.
    """

    @task()
    def get_batch() -> List[Dict[str, str]]:
        """
        #### Get Batch
        Gets a batch of unprocessed audio from quizzr server.
        Limits the output to max batch size.
        Downloads a batch of unprocessed audio from Google Drive using GoogleAPIs
        Stores the output in `default_arguments[audio_path]` location.
        """
        if os.path.exists(default_args["audio_path"]) and os.path.isdir(
            default_args["audio_path"]
        ):
            shutil.rmtree(default_args["audio_path"])
        if os.path.exists(default_args["store_path"]) and os.path.isdir(
            default_args["store_path"]
        ):
            shutil.rmtree(default_args["store_path"])
        r = requests.get(default_args["backend_url"] + "/audio/unprocessed")
        files = r.json()["result"][0 : default_args["batch_size"]]
        gdrive = drive.Drive()
        gdrive.download_batch(files, default_args["audio_path"])
        return files

    @task()
    def PreprocessData(subpath: str, mfcc_conf: str, sample_rate: int, files):
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
        return {"data": str(store_path)}

    @task()
    def SpeakerDiarization(
        store_path, detect_num_speakers=False, max_num_speakers=1, threshold=0.5
    ):
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
        store_path = store_path["data"]
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
        return {"data": rttm_path}

    @task()
    def AutomaticSpeechRecognition(store_path: str):
        store_path = store_path["data"]
        shelldon.call(
            "pipeline/asr.sh {} {}".format(
                default_args["model_directory"] + "/api.ai-kaldi-asr-model",
                os.path.join(store_path, "cleaned"),
            )
        )
        return {
            "ctm": os.path.join(store_path, "cleaned", "final.ctm"),
            "hypothesis": os.path.join(
                store_path, "cleaned", "one-best-hypothesis.txt"
            ),
        }

    @task()
    def ForcedAlignment(ctm_path: str, rttm_path: str) -> str:
        rttm_path: rttm_path["data"]
        ctm_path = ctm_path["ctm"]
        align(ctm_path, rttm_path, default_args["store_path"] + "/vtt")
        return {"data": default_args["store_path"] + "/vtt"}

    @task()
    def CalculateError(
        files: List[Dict[str, str]], hypthesis_path,
    ):
        hypthesis_path = hypthesis_path["hypothesis"]
        e = eval.accuracy(files, hypthesis_path)
        return e

    @task()
    def Upload(vtt_path: str, audio_batch: List[Dict[str, str]], score: Dict):
        vtt_path = vtt_path["data"]
        batch_number = datetime.now().strftime("%m/%d/%Y-%H:%M:%S")
        for file in audio_batch:
            file["vtt"] = open(vtt_path + "/{}.vtt".format(file["_id"]), "r").read()
            file["score"] = score[file["_id"]]
            file["batch_number"] = batch_number
            file[
                "metadata"
            ] = "detect_num_speakers=False, max_num_speakers=1, threshold=0.5"
        response = requests.post(
            default_args["backend_url"] + "/audio/processed",
            json={"result": audio_batch},
        )
        assert response.status_code == 200

    audio_batch = get_batch()
    asr_preprocessed_path = PreprocessData("asr", "asr.conf", 16000, audio_batch)
    diar_preprocessed_path = PreprocessData("diar", "mfcc.conf", 8000, audio_batch)
    asr_path = AutomaticSpeechRecognition(asr_preprocessed_path)
    rttm_path = SpeakerDiarization(diar_preprocessed_path)
    vtt_path = ForcedAlignment(asr_path, rttm_path)
    score = CalculateError(audio_batch, asr_path)
    print(score)
    Upload(vtt_path, audio_batch, score)


pipeline = quizzr_kaldi_pipeline()
