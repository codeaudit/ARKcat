from hyperopt import fmin, tpe, hp, Trials, space_eval

def get_space(num_models):
    space = {}

    for i in range(num_models):
        add_model(str(i), space)
    return space

def get_linear_model(model_num):
    return {
        'model_' + model_num: 'LR',
        'regularizer_lr_' + model_num: hp.choice('regularizer_lr_' + model_num,[
            ('l1', hp.loguniform('l1_strength_lr_' + model_num, -5,5)),
            ('l2', hp.loguniform('l2_strength_lr_' + model_num, -5,5))
            
#                    ('l1', hp.loguniform('l1_strength', np.log(1e-7), np.log(10**2))),
#                    ('l2', hp.loguniform('l2_strength', np.log(1e-7), np.log(100)))
        ]),
        'converg_tol_' + model_num: hp.loguniform('converg_tol_' + model_num, -10, -1)
    }

def get_xgboost_model(model_num):
    return {
            'model_' + model_num: 'XGBoost',
            'eta_' + model_num: hp.loguniform('eta_' + model_num,-5,0),
            'gamma_' + model_num: hp.uniform('gamma_' + model_num,0,10),
            'max_depth_' + model_num: hp.quniform('max_depth_' + model_num, 1,30,1),
            'min_child_weight_' + model_num: hp.uniform('min_child_weight_' + model_num, 0, 10),
            'max_delta_step_' + model_num: hp.uniform('max_delta_step_' + model_num, 0, 10),
            'num_round_' + model_num: hp.quniform('num_round_' + model_num, 1, 10, 1),
            'subsample_' + model_num: 1,# hp.uniform('subsample_' + model_num, .001, 1),
            'regularizer_xgb_' + model_num: hp.choice('regularizer_xgb_' + model_num,[
                ('l1', hp.loguniform('l1_strength_xgb_' + model_num, -5,5)),
                ('l2', hp.loguniform('l2_strength_xgb_' + model_num, -5,5))
                
#                    ('l1_' + model_num, hp.loguniform('l1_strength_' + model_num, np.log(1e-7), np.log(10**2))),
#                    ('l2_' + model_num, hp.loguniform('l2_strength_' + model_num, np.log(1e-7), np.log(100)))
            ])
        }


def add_model(model_num, space):
    #should take this as a param
    set_of_models = [get_linear_model(model_num)]
    space['model_' + model_num] = hp.choice('model_' + model_num, set_of_models)
    space['features_' + model_num] = {
        'nmin_to_max_' + model_num: hp.choice('nmin_to_max_' + model_num, 
                                              [(1,1),(1,2),(1,3),(2,2),(2,3)]),
        'binary_' + model_num: hp.choice('binary_' + model_num, [True, False]),
        'use_idf_' + model_num: hp.choice('transform_' + model_num, [True, False]),
        'st_wrd_' + model_num: hp.choice('st_word_' + model_num, [None, 'english'])
    }