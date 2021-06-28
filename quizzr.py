import os
from pathlib import Path, PurePath
from typing import Dict, List

import requests
from airflow.decorators import dag, task
from airflow.utils.dates import days_ago

from commands.cmd import Sox
from workflow import diar, preprocess

default_args = {
    "batch_size": 4,
    "backend_url": "http://localhost:5000",
    "audio_path": "data",
    "store_path": "processed_data",
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
        """
        r = requests.get(default_args["backend_url"])
        return r.json()[0 : default_args["batch_size"]]

    @task(multiple_outputs=True)
    def download_from_gdrive(files: List[Dict[str, str]]):
        """
        #### Download from Google Drive
        Downloads a batch of unprocessed audio from Google Drive using GoogleAPIs
        Stores the output in `default_arguments[audio_path]` location.
        """
        pass

    @task()
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
        return subpath

    @task()
    def SpeakerDiarization(
        store_path, detect_num_speakers=False, max_num_speakers=1, threshold=0.5
    ) -> str:
        """
        #### Load task
        A simple Load task which takes in the result of the Transform task and
        instead of saving it to end user review, just prints it out.
        """

        if not os.path.exists(os.path.join(store_path, "reco2num_spk")):
            with open(os.path.join(store_path, "reco2num_spk"), "w") as f:
                for file in os.listdir(os.path.join(store_path, "audio")):
                    f.write("{} {}\n".format(Path(file).stem, max_num_speakers))
        diar.diarize(store_path, detect_num_speakers, threshold)
        rttm_path = os.path.join(
            store_path, "diar", "xvectors", "plda_scores_speakers", "rttm",
        )
        if not os.path.exists(rttm_path):
            raise FileNotFoundError
        return rttm_path

    @task()
    def AutomaticSpeechRecognition():
        pass

    audio_batch = get_batch()


tutorial_etl_dag = quizzr_kaldi_pipeline()
