import random
from feature_selector import cnn_feature_selector

#random searches for a CNN
def get_cnn_model(model_num, search_space):
    feature_selector = cnn_feature_selector(search_space)
    param_dist = {'model_' + model_num: 'CNN',
            'word_vectors_' + model_num: ('word2vec', True),
            'delta_' + model_num: random.choice(feature_selector['delta_']),
            # 'flex_' + model_num: (True, random.random() * feature_selector['flex_amt_'][1]),
            'flex_' + model_num: (True, .15),
            # iden, relu, and tanh
            'activation_fn_' + model_num: random.choice(feature_selector['activation_fn_']),
            #none, clipped, or penalized
            'regularizer_cnn_' + model_num: random.choice([
                # (None, 0.0),
                ('l2', (random.random() * (feature_selector['l2_'][1] - feature_selector['l2_'][0]) + feature_selector['l2_'][0])),
                ('l2_clip', (random.random() * (feature_selector['l2_clip_'][1] - feature_selector['l2_clip_'][0]) + feature_selector['l2_clip_'][0]))
            ]),
            # 'learning_rate_' + model_num: .00025 + (random.lognormvariate(0, 1) / 370.0)
            'learning_rate_' + model_num: .0003
    }
    if len(feature_selector['dropout_']) > 1:
        param_dist['dropout_' + model_num] = random.random()
    else:
        param_dist['dropout_' + model_num] = .5
    other_hparams = {'filters_' + model_num: feature_selector['filters_'],
                    'kernel_size_' + model_num: feature_selector['kernel_size_'],
                    'kernel_increment_' + model_num: feature_selector['kernel_increment_'],
                    'kernel_num_' + model_num: feature_selector['kernel_num_'],
                    'batch_size_' + model_num: feature_selector['batch_size_']}
    for label, element in other_hparams.iteritems():
        try:
             param_dist[label] = random.randint(*element)
        except TypeError:
             param_dist[label] = element
    return param_dist

def get_feats(model_num):
    return {'nmin_to_max_' + model_num: random.choice([(1,1),(1,2),(1,3),(2,2),(2,3)]),
            'binary_' + model_num: random.choice([True, False]),
            'use_idf_' + model_num: random.choice([True, False]),
            'st_wrd_' + model_num: random.choice([None, 'english'])}