# Quizzr Kaldi Pipeline
This is a simple Apache Airflow pipeline using the TaskFlow API. It fetches a batch of unprocessed audio from the main Quizzr server, downloads the audio from Google Drive, processes the audio using Kaldi (VAD,DIAR,ASR) and uploads the generated WebVTT transcripts to the main Quizzr server.
## Installation (WIP)
Prior to installation, you will need to have Python and Miniconda installed on Linux.

1. Clone the repository with Git.
1. Go into the directory of the repository and run `download.sh`.
1. Install the dependencies from `requirements.txt` by executing `conda create --env <env-name> --file requirements.txt` in the terminal. Replace `<env-name>` with the name of the virtual environment you want to create.
1. Append to your `.bashrc` file (located in the home directory of your account) `source /path/to/quizzr-pipeline/path.sh`.
1. Make a directory to the airflow home and copy `airflow.cfg` from the `docker` directory of the repository to that location. Set the environment variable `AIRFLOW_HOME` to `/path/to/airflow`.
1. Execute `airflow db init`, then execute `airflow users create`, specifying the `--username`, `--firstname`, `--lastname`, `role`, `email`, and `password` arguments.
1. Install `supervisor` by executing `pip install supervisor`.
## Usage (WIP)
Execute `supervisord -c /path/to/quizzr-pipeline/docker/supervisord.conf`.
## Using Docker
If you have Docker installed, you can install this repository by running the Dockerfile in the `docker` directory.