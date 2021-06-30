import os

from commands import shelldon


def diarize(store_path, detect_num_speakers=False, threshold=0.5):
    cleaned_path = os.path.join(store_path, "cleaned")
    shelldon.call(
        "local/nnet3/xvector/prepare_feats.sh --nj 1 {0} {1}/cmnn {1}/cmnn".format(
            cleaned_path, store_path
        )
    )
    shelldon.call("cp {0}/cleaned/segments {0}/cmnn/segments".format(store_path))
    shelldon.call(
        "diarization/nnet3/xvector/extract_xvectors.sh --nj 1 --window 1.5 --period 0.75 --apply-cmn false models/0003_sre16_v2_1a/exp/xvector_nnet_1a {0}/cmnn {0}/xvectors".format(
            store_path
        )
    )
    shelldon.call(
        "diarization/nnet3/xvector/score_plda.sh --target-energy 0.9 --nj 1 models/0003_sre16_v2_1a/exp/xvectors_sre_combined/ {0}/xvectors {0}/xvectors/plda_scores".format(
            store_path
        )
    )
    if not detect_num_speakers:
        shelldon.call(
            "diarization/cluster.sh --nj 1 --reco2num-spk {0}/reco2num_spk {0}/xvectors/plda_scores {0}/xvectors/plda_scores_speakers".format(
                store_path
            )
        )
    else:
        shelldon.call(
            "diarization/cluster.sh --nj 1 --threshold {0} {1}/xvectors/plda_scores {1}/xvectors/plda_scores_speakers".format(
                threshold, store_path
            )
        )

