import numpy as np
import tensorflow as tf
from cnn_methods import *
from cnn_class import CNN
import cnn_eval
import time, resource
import inspect_checkpoint

def l2_loss_float(W):
    return tf.cast(tf.scalar_mul(tf.convert_to_tensor(2.0), tf.nn.l2_loss(W)), tf.float32_ref)


def main(params, input_X, input_Y, key_array, model_dir):

    train_X, train_Y, val_X, val_Y = separate_train_and_val(input_X, input_Y)

    cnn_dir = '../output/temp/'
    with tf.Graph().as_default():
        with open(cnn_dir + 'train_log', 'a') as timelog:
            timelog.write('\n\n\nNew Model:')
            max_index = 0
            for example in train_X:
                if np.count_nonzero(example) == 0:
                    print 'error: zero entry'
                max_index = max(np.amax(example), max_index)
            # print 'max index', max_index
            # print key_array.shape
                # else:
                    # print 'maximum', np.amax(example)
                    # print 'shape', example.shape
            cnn = CNN(params, key_array)
            loss = cnn.cross_entropy

            #it's not this part
            # loss += tf.mul(tf.constant(params['REG_STRENGTH']), cnn.reg_loss)
            #problem: thinks loss is None
            # print loss
            #not the optimizer
            grads_and_vars = cnn.optimizer.compute_gradients(cnn.cross_entropy)
            # print grads_and_vars
            cnn.optimizer.apply_gradients(grads_and_vars)
            train_step = cnn.optimizer.minimize(loss)
            sess = tf.Session(config=tf.ConfigProto(inter_op_parallelism_threads=1,
                                  intra_op_parallelism_threads=1, use_per_session_threads=True))
            sess.run(tf.initialize_all_variables())
            saver = tf.train.Saver(tf.all_variables())
            path = saver.save(sess, cnn_dir + 'cnn_eval_epoch%i' %0)
            # reader = tf.train.NewCheckpointReader(path)
            # print(reader.debug_string().decode("utf-8"))
            best_dev_accuracy = cnn_eval.float_entropy(path, val_X, val_Y, key_array, params)
            timelog.write( '\ndebug acc %g' %best_dev_accuracy)
            timelog.write('\n%g'%time.clock())
            for epoch in range(params['EPOCHS']):
                batches_x, batches_y = scramble_batches(params, train_X, train_Y)
                for j in range(len(batches_x)):
                    feed_dict = {cnn.input_x: batches_x[j], cnn.input_y: batches_y[j],
                                 cnn.dropout: params['TRAIN_DROPOUT'], cnn.word_embeddings_new: np.zeros([0, key_array.shape[1]])}
                    train_step.run(feed_dict=feed_dict, session=sess)
                    #apply l2 clipping to weights and biases
                    if params['REGULARIZER'] == 'l2_clip':
                        if j == (len(batches_x) - 2):
                            print 'debug clip_vars'
                            check_weights = tf.reduce_sum(cnn.weights[0]).eval(session=sess)
                            check_biases = tf.reduce_sum(cnn.biases[0]).eval(session=sess)
                            check_Wfc = tf.reduce_sum(cnn.W_fc).eval(session=sess)
                            check_bfc = tf.reduce_sum(cnn.b_fc).eval(session=sess)
                            cnn.clip_vars(params)
                            weights_2 = tf.reduce_sum(cnn.weights[0]).eval(session=sess)
                            biases_2 = tf.reduce_sum(cnn.biases[0]).eval(session=sess)
                            Wfc_2 = tf.reduce_sum(cnn.W_fc).eval(session=sess)
                            bfc_2 = tf.reduce_sum(cnn.b_fc).eval(session=sess)
                            if np.array_equal(check_weights, weights_2):
                                print 'clipped'
                            elif np.array_equal(check_biases, biases_2):
                                print 'clipped'
                            elif np.array_equal(check_Wfc, Wfc_2):
                                print 'clipped'
                            elif np.array_equal(check_bfc, bfc_2):
                                print 'clipped'
                            else:
                                print 'no clip. means:'
                            print l2_loss_float(cnn.weights[0]).eval(session=sess)
                            print l2_loss_float(cnn.biases[0]).eval(session=sess)
                            print l2_loss_float(cnn.W_fc).eval(session=sess)
                            print l2_loss_float(cnn.b_fc).eval(session=sess)
                        else:
                            cnn.clip_vars(params)
                timelog.write('\n\nepoch %i initial time %g' %(epoch, time.clock()))
                timelog.write('\nCPU usage: %g'
                            %(resource.getrusage(resource.RUSAGE_SELF).ru_utime +
                            resource.getrusage(resource.RUSAGE_SELF).ru_stime))
                timelog.write('\nmemory usage: %g' %(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
                checkpoint = saver.save(sess, cnn_dir + 'cnn_eval_epoch%i' %epoch)
                dev_accuracy = cnn_eval.float_entropy(path, val_X, val_Y, key_array, params)
                timelog.write('\ndev accuracy: %g'%dev_accuracy)
                if dev_accuracy > best_dev_accuracy:
                    path = saver.save(sess, model_dir + '/cnn', global_step=epoch)
                    best_dev_accuracy = dev_accuracy
                    if dev_accuracy < best_dev_accuracy - .02:
                        #early stop if accuracy drops significantly
                        return path, cnn.weighted_word_embeddings.eval(session=sess)
            return path, cnn.weighted_word_embeddings.eval(session=sess)

if __name__ == "__main__":
    main()
