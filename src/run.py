import os, sys
import codecs
import datetime
import cPickle as pickle
import Queue as queue

from optparse import OptionParser
import numpy as np
from hyperopt import fmin, tpe, hp, Trials, space_eval

import classify_test
import space_manager_cnn

data_filename = None
label_filename = None
feature_dir = None
output_dir = None
log_filename = None

def call_experiment(args):
    print 'debug'
    global trial_num
    trial_num = trial_num + 1

    feats_and_args = {}
    all_description = []
    for i in range(num_models):
        feature_list, description, kwargs = wrangle_params(args, str(i))
        all_description = all_description + description
        feats_and_args[i] = {'feats':feature_list, 'params':kwargs}


    result = classify_test.classify(train_data_filename, train_label_filename, dev_data_filename,
                                    dev_label_filename, train_feature_dir, dev_feature_dir,
                                    feats_and_args, folds=num_folds)



    with codecs.open(log_filename, 'a') as output_file:
        output_file.write(str(datetime.datetime.now()) + '\t' + ' '.join(all_description) +
                          '\t' + str(-result['loss']) + '\n')
    save_model(result)

    print("\nFinished iteration " + str(trial_num) + ".\n\n\n")
    sys.stdout.flush()
    return result

#have to edit features--cnn won't take idf, for example
def wrangle_params(args, model_num):
    kwargs = {}

    print('')
    print('the args:')
    print(args)


    model = args['model_' + model_num]['model_' + model_num]
    kwargs['model_type'] = model
    if model == 'LR':
        kwargs['regularizer'] = args['model_' + model_num]['regularizer_lr_' + model_num][0]
        kwargs['alpha'] = args['model_' + model_num]['regularizer_lr_' + model_num][1]
        kwargs['converg_tol'] = args['model_' + model_num]['converg_tol_' + model_num]
    elif  model == 'XGBoost':
        kwargs['eta'] = args['model_' + model_num]['eta_' + model_num]
        kwargs['gamma'] = args['model_' + model_num]['gamma_' + model_num]
        kwargs['max_depth'] = int(args['model_' + model_num]['max_depth_' + model_num])
        kwargs['min_child_weight'] = args['model_' + model_num]['min_child_weight_' + model_num]
        kwargs['max_delta_step'] = args['model_' + model_num]['max_delta_step_' + model_num]
        kwargs['subsample'] = args['model_' + model_num]['subsample_' + model_num]
        kwargs['regularizer'] = args['model_' + model_num]['regularizer_xgb_' + model_num][0]
        kwargs['reg_strength'] = args['model_' + model_num]['regularizer_xgb_' + model_num][1]
        kwargs['num_round'] = int(args['model_' + model_num]['num_round_' + model_num])
    elif model == 'CNN':
        kwargs['word_vector_init'] = args['model_' + model_num]['word_vectors_' + model_num][0]
        kwargs['word_vector_update'] = args['model_' + model_num]['word_vectors_' + model_num][1]
        kwargs['delta'] = args['model_' + model_num]['delta_' + model_num]
        kwargs['flex'] = int(args['model_' + model_num]['flex_' + model_num])
        kwargs['kernel_size_1'] = int(args['model_' + model_num]['kernel_size_1_' + model_num])
        kwargs['kernel_size_2'] = int(args['model_' + model_num]['kernel_size_2_' + model_num])
        kwargs['kernel_size_3'] = int(args['model_' + model_num]['kernel_size_3_' + model_num])
        # kwargs['num_kernels'] = args['model_' + model_num]['num_kernels_' + model_num][0]
        kwargs['filters'] = int(args['model_' + model_num]['filters_' + model_num])
        kwargs['dropout'] = args['model_' + model_num]['dropout_' + model_num]
        kwargs['batch_size'] = int(args['model_' + model_num]['batch_size_' + model_num])
        kwargs['activation_fn'] = args['model_' + model_num]['activation_fn_' + model_num]
        kwargs['regularizer'] = args['model_' + model_num]['regularizer_cnn_' + model_num][0]
        kwargs['reg_strength'] = args['model_' + model_num]['regularizer_cnn_' + model_num][1]
        kwargs['learning_rate'] = args['model_' + model_num]['learning_rate_' + model_num]
        # for i in xrange(args['model_' + model_num]['num_kernels_' + model_num][0]):
        #     kwargs['kernel_size_' + i] = args['model_' + model_num]['num_kernels_' + model_num][1]


    features = {}
    features['ngram_range'] = args['features_' + model_num]['nmin_to_max_' + model_num]
    features['binary'] = args['features_' + model_num]['binary_' + model_num]
    features['use_idf'] = args['features_' + model_num]['use_idf_' + model_num]
    features['stop_words'] = args['features_' + model_num]['st_wrd_' + model_num]


    print kwargs
    print features
    description = [str(k) + '=' + str(v) for (k, v) in kwargs.items()]
    description[0] = description[0] + ',' + [str(k) + '=' + str(v) for (k, v) in features.items()][0]
    return features, description, kwargs


def save_model(result):
    model = result['model']
    feature_list = result['model'].feats_and_params[0]['feats']
    model_hyperparams = result['model'].feats_and_params[0]['params']
    #STUPID FILENAMES TOO LONG
    short_name = {'model_type':'mdl', 'regularizer':'rg', 'converg_tol':'cvrg','alpha':'alpha',
                  'eta':'eta', 'gamma':'gamma', 'max_depth':'dpth', 'min_child_weight':'mn_wght',
                  'max_delta_step':'mx_stp', 'subsample':'smpl', 'reg_strength':'rg_str',
                  'num_round':'rnds', 'lambda':'lmbda', 'ngram_range':'ngrms', 'binary':'bnry',
                  'use_idf':'idf', 'stop_words':'st_wrd', 'word_vector_init' : 'wv_init',
                  'word_vector_update' : 'upd', 'delta': 'delta', 'flex': 'flex',
                  'kernel_size_1':'ks1', 'kernel_size_2' :'ks2', 'kernel_size_3': 'ks3',
                  'filters': 'fltrs', 'dropout': 'dropout', 'batch_size' : 'batch_size',
                  'activation_fn': 'actvn_fn', 'regularizer':'rg', 'reg_strength':'rg_str',
                  'learning_rate': 'learn_rt'}

    # to save the model after each iteration
    feature_string = ''
    for feat, value in feature_list.items():
        feature_string = feature_string + short_name[feat] + '=' + str(value) + ';'
    for hparam in model_hyperparams:
        cur_hparam = None
        #DEBUGGING
        if hparam == 'folds':
            continue
        if isinstance(model_hyperparams[hparam], float):
            cur_hparam = str(round(model_hyperparams[hparam]*1000)/1000)
        else:
            cur_hparam = str(model_hyperparams[hparam])
        feature_string = feature_string + short_name[hparam] + '=' + cur_hparam + ';'
    feature_string = feature_string[:-1]
    pickle.dump([trial_num, train_feature_dir, result], open(model_dir + str(trial_num) + '_' +
                                                             feature_string + '.model', 'wb'))



#sets the global variables, including params passed as args
def set_globals():
    usage = "%prog train_text.json train_labels.csv dev_text.json dev_labels.csv output_dir"
    parser = OptionParser(usage=usage)
    parser.add_option('-m', dest='max_iter', default=30,
                      help='Maximum iterations of Bayesian optimization; default=%default')

    (options, args) = parser.parse_args()

    global train_data_filename, train_label_filename, dev_data_filename, dev_label_filename
    global output_dir, train_feature_dir, dev_feature_dir, model_dir, log_filename, trial_num, max_iter
    global num_models, model_types, num_folds

    train_data_filename = args[0] + 'train.data'
    train_label_filename = args[0] + 'train.labels'
    dev_data_filename = args[0] + 'dev.data'
    dev_label_filename = args[0] + 'dev.labels'
    output_dir = args[1]
    num_models = int(args[2])
    model_types = args[3].split('-')
    num_folds = int(args[4])
    print('train data filename: ',train_data_filename)

    train_feature_dir = output_dir + '/train_features/'
    dev_feature_dir = output_dir + '/dev_train_features/'
    model_dir = output_dir + '/saved_models/'

    trial_num = 0
    max_iter = int(options.max_iter)

    for directory in [output_dir, train_feature_dir, dev_feature_dir, model_dir]:
        if not os.path.exists(directory):
            os.makedirs(directory)
    log_filename = os.path.join(output_dir, 'log.txt')

    print dev_data_filename

    with open(log_filename, 'w') as logfile:
        logfile.write(','.join([train_data_filename, train_label_filename, dev_data_filename,
                                dev_label_filename, train_feature_dir, dev_feature_dir, output_dir]) + '\n')


def printing_best(trials):
    priority_q = queue.PriorityQueue()
    losses = trials.losses()
    for i in range(len(losses)):
        priority_q.put((losses[i], i))
    print('top losses and settings: ')
    for i in range(0,min(3,max_iter)):
        index = priority_q.get()[1]
        print(losses[index])
        print(trials.trials[index]['misc']['vals'])
        print('')
    print('')


def main():
    print("Made it to the start of main!")
    set_globals()
    trials = Trials()
    space = space_manager_cnn.get_space(num_models, model_types)
    best = fmin(call_experiment,
                space=space,
                algo=tpe.suggest,
                max_evals=max_iter,
                trials=trials)

    print space_eval(space, best)
    printing_best(trials)


if __name__ == '__main__':
    main()
