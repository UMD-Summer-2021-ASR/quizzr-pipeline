FROM kaldiasr/kaldi:latest
RUN apt update
WORKDIR /home/root
RUN git clone https://github.com/UMD-Summer-2021-ASR/quizzr-pipeline
WORKDIR /home/root/quizzr-pipeline
RUN bash download.sh
RUN apt install -y curl
RUN curl https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh --output miniconda.sh
RUN bash miniconda.sh -b
ENV PATH="/root/miniconda3/bin:$PATH"
COPY pipeline.yml pipeline.yaml
RUN conda env update -n base --file pipeline.yaml 
ENV PATH="/root/miniconda3/bin:$PATH:/opt/kaldi"
COPY path.sh /home/root/path.sh
COPY path.sh /home/root/quizzr-pipeline/path.sh
RUN echo "source /home/root/path.sh" >> /root/.bashrc
ADD airflow.cfg  /root/airflow/airflow.cfg
ADD webserver_config.py /root/airflow/webserver_config.py
ENV AIRFLOW_HOME=/root/airflow
RUN airflow db init
RUN airflow users create --username admin3  --firstname Peter  --lastname Parker --role Admin  --email admin3@superhero.org --password admin
RUN python -m pip install supervisor
COPY supervisord.conf /etc/supervisor/supervisord.conf
CMD [ "supervisord","-c" ,"/etc/supervisor/supervisord.conf" ]
