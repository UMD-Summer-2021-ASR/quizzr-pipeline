mkdir -p temp
mkdir -p models
cd temp
wget https://github.com/api-ai/api-ai-english-asr-model/releases/download/1.0/api.ai-kaldi-asr-model.zip
wget https://kaldi-asr.org/models/3/0003_sre16_v2_1a.tar.gz 
unzip  api.ai-kaldi-asr-model.zip -d ../models/
tar -xzf 0003_sre16_v2_1a.tar.gz -C ../models/
cd ..
rm -rf temp