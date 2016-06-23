import numpy as np
import tensorflow as tf
import text_cnn_methods_temp
from text_cnn_model_temp import CNN
import sys

# def flex(input_list, params):
#     for example in input_list:
#         #20% chance of padding the left side
#         if boolean_percent(15):
#             example = insert_padding(example, params['FLEX'], True, params['WORD_VECTOR_LENGTH'])
#         elif boolean_percent(15):
#             example = insert_padding(example, math.ceil(params['FLEX']/2.0), True, params['WORD_VECTOR_LENGTH'])
#         #20% chance of padding the right
#         if boolean_percent(15):
#             example = insert_padding(example, params['FLEX'], False, params['WORD_VECTOR_LENGTH'])
#         elif boolean_percent(15):
#             example = insert_padding(example, math.ceil(params['FLEX']/2.0), False, params['WORD_VECTOR_LENGTH'])
#     return input_list
#
# def insert_padding(example, tokens_to_pad, left, length):
#     if left:
#         for i in range(tokens_to_pad):
#             example.insert(0, [0] * length)
#     else:
#         for i in range(tokens_to_pad):
#             example.append([0] * length)
#     return example

def flex(input_list, params):
    for example in input_list:
        #20% chance of padding the left side
        if boolean_percent(15):
            example = insert_padding(example, params['FLEX'], True)
        elif boolean_percent(15):
            example = insert_padding(example, math.ceil(params['FLEX']/2.0), True)
        #20% chance of padding the right
        if boolean_percent(15):
            example = insert_padding(example, params['FLEX'], False)
        elif boolean_percent(15):
            example = insert_padding(example, math.ceil(params['FLEX']/2.0), False)
    return input_list

def insert_padding(example, tokens_to_pad, left):
    if left:
        for i in range(tokens_to_pad):
            example.insert(0, 0)
    else:
        for i in range(tokens_to_pad):
            example.append(0)
    return example

#convert x to multidimensional python list if necessary
def scramble_batches(params, x, y):
    extras = len(x) % params['BATCH_SIZE']
    x, y = text_cnn_methods_temp.shuffle_in_unison(x, y)
    duplicates_x = []
    duplicates_y = []
    for i in range(extras):
        duplicates_x.append(x[i])
        duplicates_y.append(y[i])
    x.extend(duplicates_x)
    y.extend(duplicates_y)
    if params['FLEX'] > 0:
        x = flex(x, params)
    # if len(x) > params['MAX_EPOCH_SIZE']:
    #     extras = params['MAX_EPOCH_SIZE'] % params['BATCH_SIZE']
    #     x = x[:(params['MAX_EPOCH_SIZE']) - extras]
    #     y = y[:(params['MAX_EPOCH_SIZE']) - extras]
    #     incomplete = False
    x, y = sort_examples_by_length(x, y)
    batches_x, batches_y = [], []
    while len(y) >= params['BATCH_SIZE']:
        batches_x.append(pad_all(x[:params['BATCH_SIZE']]))
        batches_y.append(np.asarray(y[:params['BATCH_SIZE']]))
        x = x[params['BATCH_SIZE']:]
        y = y[params['BATCH_SIZE']:]
    return batches_x, batches_y

def sort_examples_by_length(x, y):
    lengths = []
    for i in range(len(x)):
        lengths.append(len(x[i]))
    new_lengths = []
    new_x = []
    new_y = []
    for i in range(len(lengths)):
        for j in range(len(new_lengths)):
            if lengths[i] < new_lengths[j]:
                new_lengths.insert(j, lengths[i])
                new_x.insert(j, x[i])
                new_y.insert(j, y[i])
                break
        else:
            new_lengths.append(lengths[i])
            new_x.append(x[i])
            new_y.append(y[i])
    return new_x, new_y

#takes tokenized list_of_examples and pads all to the maximum length
def pad_all(list_of_examples, params):
    max_length = get_max_length(list_of_examples)
    for i in range(len(list_of_examples)):
        list_of_examples[i] = pad_one(list_of_examples[i], max_length, params)
    return list_of_examples

def get_max_length(list_of_examples):
    max_length = 0
    for line in list_of_examples:
        max_length = max(max_length, len(line))
    return max_length

#pads all sentences to same length
def pad_one(list_of_word_vecs, max_length, params):
    left = (max_length - len(list_of_word_vecs)) / 2
    right = left
    if (max_length - len(list_of_word_vecs)) % 2 != 0:
        right += 1
    for i in range(left):
        list_of_word_vecs.insert(0, 0)
        # list_of_word_vecs.insert(0, [0] * params['WORD_VECTOR_LENGTH'])
    for i in range(right):
        list_of_word_vecs.append(0)
        # list_of_word_vecs.append([0] * params['WORD_VECTOR_LENGTH'])
    return list_of_word_vecs

def init_key_array(vocab_size, params): # vocab):
    key_list = []
    if params['USE_WORD2VEC'] == False:
        for i in range(vocab_size):
            key_list.append(np.random.uniform(-0.25,0.25, params['WORD_VECTOR_LENGTH']))
    else:
        key_list = [0] * vocab_size
        with open(params['WORD_VECS_FILE_NAME'], 'r') as word2vec:
            word2vec.readline()
            for i in range(3000000):   #number of words in word2vec
                line = tokenize(word2vec.readline().strip())
                #turn into floats
                if line[0] in vocab:
                    vector = []
                    for num in line[1:]:
                        vector.append(float(num))
                    if len(vector) != params['WORD_VECTOR_LENGTH']:
                        raise ValueError
                    key_list[vocab.index(line[0])] = np.asarray(vector)
        for element in key_list:
            try:
                element.shape
            except TypeError:
                element = np.random.uniform(-0.25,0.25,params['WORD_VECTOR_LENGTH'])
        key_list.insert(0, [0] * params['WORD_VECTOR_LENGTH'])
        return np.asarray(key_list)

def to_dense(train_X):
    for example in train_X:
        example = example.nonzero()[1].tolist()
        for word in example:
            word += 1
        example = np.asarray(example)
    return train_X

#train_x is a python list of numpy arrays containing sentences as word vectors
def main(params, train_x, train_y, val_X, val_Y, key_array):
    with tf.Graph().as_default():
        cnn = CNN(params, key_array)
        loss = tf.reduce_sum(cnn.cross_entropy)
        loss += tf.scalar_mul(tf.constant(params['REG_STRENGTH']), cnn.reg_loss)
        train_step = cnn.optimizer.minimize(loss)
        saver = tf.train.Saver(tf.all_variables())
        #run session
        sess = tf.Session(config=tf.ConfigProto(inter_op_parallelism_threads=1,
                          intra_op_parallelism_threads=1, use_per_session_threads=True))
        sess.run(tf.initialize_all_variables())
        best_dev_accuracy = cnn_eval.evaluate(cnn, val_X, val_Y, params, sess, cross_entropy=True)
        for i in range(params['EPOCHS']):
            params['epoch'] = i + 1
            batches_x, batches_y = scramble_batches(params, train_x, train_y)
            for j in range(len(batches_x)):
                feed_dict = {cnn.input_x: batches_x[j], cnn.input_y: batches_y[j],
                             cnn.dropout: params['TRAIN_DROPOUT']}
                train_step.run(feed_dict=feed_dict, session = sess)
                #apply l2 clipping to weights and biases
                if params['REGULARIZER'] = 'l2_clip':
                    cnn.clip_vars(params)
            dev_accuracy = cnn_eval.evaluate(cnn, val_X, val_Y, params, sess, cross_entropy=True)
            if dev_accuracy < best_dev_accuracy:
                #!!!
                checkpoint = saver.save(sess, 'text_cnn_run' + , global_step = params['epoch'])
                best_dev_accuracy = dev_accuracy
                if dev_accuracy < best_dev_accuracy - .02:
                    #early stop if accuracy drops significantly
                    return checkpoint
        return checkpoint

if __name__ == "__main__":
    main()
