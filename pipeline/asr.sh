#!/bin/bash

. ./path.sh
MODEL_DIR=$1
DATA_DIR=$2

for file in final.mdl HCLG.fst words.txt frame_subsampling_factor; do
  if [ ! -f $MODEL_DIR/$file ]; then
    echo "$MODEL_DIR/$file not found, use ./download-model.sh"
    exit 1;
  fi
done;

for app in nnet3-latgen-faster apply-cmvn lattice-scale; do
  command -v $app >/dev/null 2>&1 || { echo >&2 "$app not found, is kaldi compiled?"; exit 1; }
done;

steps/make_mfcc.sh --nj 1 --mfcc-config $MODEL_DIR/mfcc.conf \
      --cmd "run.pl" $DATA_DIR || { echo "Unable to calculate mfcc, ensure 16kHz, 16 bit little-endian wav format or see log"; exit 1; };

steps/compute_cmvn_stats.sh $DATA_DIR || exit 1;
compute-mfcc-feats \
    --config=$MODEL_DIR/mfcc.conf \
    scp:$DATA_DIR/wav.scp \
    ark,scp:$DATA_DIR/feats.ark,$DATA_DIR/feats.scp


frame_subsampling_factor=$(cat $MODEL_DIR/frame_subsampling_factor)

nnet3-latgen-faster --frame-subsampling-factor=1 --frames-per-chunk=50 --extra-left-context=0 \
 --extra-right-context=0 --extra-left-context-initial=-1 --extra-right-context-final=-1 \
 --minimize=false --max-active=7000 --min-active=200 --beam=15.0 --lattice-beam=8.0 \
 --acoustic-scale=1.0 --allow-partial=true \
 --word-symbol-table=$MODEL_DIR/words.txt $MODEL_DIR/final.mdl $MODEL_DIR/HCLG.fst \
  "ark:$DATA_DIR/feats.ark" \
  "ark,t:$DATA_DIR/lattices.ark"

lattice-1best --acoustic-scale=1.0 ark:$DATA_DIR/lattices.ark  ark:- | nbest-to-ctm ark:- $DATA_DIR/out.ctm

cat $DATA_DIR/out.ctm | int2sym.pl -f 5 $MODEL_DIR/words.txt > $DATA_DIR/final.ctm

lattice-best-path \
    --word-symbol-table=$MODEL_DIR/words.txt \
    ark:$DATA_DIR/lattices.ark \
    ark,t:$DATA_DIR/one-best.tra;

utils/int2sym.pl -f 2- \
    $MODEL_DIR/words.txt \
    $DATA_DIR/one-best.tra \
    > $DATA_DIR/one-best-hypothesis.txt;
