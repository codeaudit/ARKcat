DATASET='/home/katya/datasets/sst2/'
W2V_LOC='/home/katya/datasets/sst2_vecs.txt'
SAVE_LOC='../output/'$1
SEARCH_TYPE='grid'
SEARCH_SPACE='small'
NUM_MODELS='1'
MODEL_FILE=~/datasets/$SEARCH_TYPE'_'$SEARCH_SPACE'_linear_'$NUM_MODELS'.models'

echo $MODEL_FILE
rm $MODEL_FILE
echo "creating models..."

python print_grid_or_rand_search.py '--'$SEARCH_TYPE $SEARCH_SPACE 'linear'

echo $SAVE_LOC
rm -rf $SAVE_LOC
echo "making the dir to save output..."
mkdir -p $SAVE_LOC /

echo "about to run.py"
for ((i=0; i<=$NUM_MODELS; i++)); do
  python run.py $DATASET $W2V_LOC $SAVE_LOC 5 -f $MODEL_FILE $i >> $SAVE_LOC/'outfile.txt' 2>> $SAVE_LOC/'errfile.txt'
done

echo "done with run.py. now going to eval.py"
python eval.py $SAVE_LOC/saved_models/ $DATASET $SAVE_LOC/ >> $SAVE_LOC/'outfile.txt' 2>> $SAVE_LOC/'errfile.txt'
echo "done with eval.py"


""" high level on stampede:
dir for ceil(iters/16)
script to run 16
save to dir as 0_0-0_15
then next file 1_0-1_15
etc.
eval all dirs in save_dir

todo:
stampede codec
technical writeup
where to mkdirs?
why 6 procs instead of 4?? 3 "3" and 3 "2"
  I'm limiting the same way, but it's not limiting, as if paralellized to 3 ???
  Not "adding" to CPU usage of highest processed
  but not saving model of its own
  im stumped :(
  didn't happen when I run manually, I don't think

done:
eval.py (for the moment)
w2v processing"""
