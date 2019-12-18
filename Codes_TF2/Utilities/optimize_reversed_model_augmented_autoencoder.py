#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Nov 23 10:53:31 2019

@author: hwan
"""
import sys
sys.path.append('../..')

import shutil # for deleting directories
import os
import time

import tensorflow as tf
import numpy as np
from Thermal_Fin_Heat_Simulator.Utilities.forward_solve import Fin
from Thermal_Fin_Heat_Simulator.Utilities.thermal_fin import get_space_2D, get_space_3D

import pdb #Equivalent of keyboard in MATLAB, just add "pdb.set_trace()"

###############################################################################
#                             Training Properties                             #
###############################################################################
def optimize(hyperp, run_options, file_paths, NN, obs_indices, loss_autoencoder, loss_model_augmented, relative_error, parameter_and_state_obs_train, parameter_and_state_obs_val, parameter_and_state_obs_test, parameter_dimension, num_batches_train):
    #=== Generate Dolfin Function Space and Mesh ===#
    if run_options.fin_dimensions_2D == 1:
        V, mesh = get_space_2D(40)
    if run_options.fin_dimensions_3D == 1:    
        V, mesh = get_space_3D(40)
    solver = Fin(V)
    print(V.dim())  
    
    #=== Optimizer ===#
    optimizer = tf.keras.optimizers.Adam()

    #=== Define Metrics ===#
    mean_loss_train = tf.keras.metrics.Mean()
    mean_loss_train_autoencoder = tf.keras.metrics.Mean() 
    mean_loss_train_model_augmented = tf.keras.metrics.Mean()
    
    mean_loss_val = tf.keras.metrics.Mean()
    mean_loss_val_autoencoder = tf.keras.metrics.Mean()
    mean_loss_val_model_augmented = tf.keras.metrics.Mean()
    
    mean_loss_test = tf.keras.metrics.Mean()
    mean_loss_test_autoencoder = tf.keras.metrics.Mean()
    mean_loss_test_model_augmented = tf.keras.metrics.Mean()    
    
    mean_relative_error_state_autoencoder = tf.keras.metrics.Mean()
    mean_relative_error_state_forward_problem = tf.keras.metrics.Mean()
    mean_relative_error_parameter = tf.keras.metrics.Mean()
    
    #=== Initialize Metric Storage Arrays ===#
    storage_array_loss_train = np.array([])
    storage_array_loss_train_autoencoder = np.array([])
    storage_array_loss_train_model_augmented = np.array([])
    
    storage_array_loss_val = np.array([])
    storage_array_loss_val_autoencoder = np.array([])
    storage_array_loss_val_model_augmented = np.array([])
    
    storage_array_loss_test = np.array([])
    storage_array_loss_test_autoencoder = np.array([])
    storage_array_loss_test_model_augmented = np.array([])
    
    storage_array_relative_error_state_autoencoder = np.array([])
    storage_array_relative_error_state_forward_problem = np.array([])
    storage_array_relative_error_parameter = np.array([])
    
    #=== Creating Directory for Trained Neural Network ===#
    if not os.path.exists(file_paths.NN_savefile_directory):
        os.makedirs(file_paths.NN_savefile_directory)
    
    #=== Tensorboard ===# Tensorboard: type "tensorboard --logdir=Tensorboard" into terminal and click the link
    if os.path.exists(file_paths.tensorboard_directory): # Remove existing directory because Tensorboard graphs mess up of you write over it
        shutil.rmtree(file_paths.tensorboard_directory)  
    summary_writer = tf.summary.create_file_writer(file_paths.tensorboard_directory)

###############################################################################
#                   Training, Validation and Testing Step                     #
###############################################################################
    #=== Train Step ===#
    #@tf.function
    def train_step(batch_parameter_train, batch_state_obs_train):
        with tf.GradientTape() as tape:
            batch_state_pred_train_AE = NN(batch_state_obs_train)
            batch_parameter_pred_train = NN.encoder(batch_state_obs_train)
            batch_loss_train_autoencoder = loss_autoencoder(batch_state_pred_train_AE, batch_state_obs_train)
            batch_loss_train_model_augmented = loss_model_augmented(hyperp, run_options, V, solver, obs_indices, batch_state_obs_train, batch_parameter_pred_train, hyperp.penalty_aug)
            batch_loss_train = batch_loss_train_autoencoder + batch_loss_train_model_augmented
        gradients = tape.gradient(batch_loss_train, NN.trainable_variables)
        optimizer.apply_gradients(zip(gradients, NN.trainable_variables))
        mean_loss_train(batch_loss_train)
        mean_loss_train_autoencoder(batch_loss_train_autoencoder)
        mean_loss_train_model_augmented(batch_loss_train_model_augmented)
        return gradients

    #=== Validation Step ===#
    #@tf.function
    def val_step(batch_parameter_val, batch_state_obs_val):
        batch_state_pred_val_AE = NN(batch_state_obs_val)
        batch_parameter_pred_val = NN.encoder(batch_state_obs_val)
        batch_loss_val_autoencoder = loss_autoencoder(batch_state_pred_val_AE, batch_state_obs_val)
        batch_loss_val_model_augmented = loss_model_augmented(hyperp, run_options, V, solver, obs_indices, batch_state_obs_val, batch_parameter_pred_val, hyperp.penalty_aug)
        batch_loss_val = batch_loss_val_autoencoder + batch_loss_val_model_augmented
        mean_loss_val_autoencoder(batch_loss_val_autoencoder)
        mean_loss_val_model_augmented(batch_loss_val_model_augmented)
        mean_loss_val(batch_loss_val)     
    
    #=== Test Step ===#
    #@tf.function
    def test_step(batch_parameter_test, batch_state_obs_test):
        batch_state_pred_test_AE = NN(batch_state_obs_test)
        batch_state_pred_test_forward_problem = NN.decoder(batch_parameter_test)
        batch_parameter_pred_test = NN.encoder(batch_state_obs_test)
        batch_loss_test_autoencoder = loss_autoencoder(batch_state_pred_test_AE, batch_state_obs_test)
        batch_loss_test_model_augmented = loss_model_augmented(hyperp, run_options, V, solver, obs_indices, batch_state_obs_test, batch_parameter_pred_test, hyperp.penalty_aug)
        batch_loss_test = batch_loss_test_autoencoder + batch_loss_test_model_augmented
        mean_loss_test_autoencoder(batch_loss_test_autoencoder)
        mean_loss_test_model_augmented(batch_loss_test_model_augmented)
        mean_loss_test(batch_loss_test)
        mean_relative_error_state_autoencoder(relative_error(batch_state_pred_test_AE, batch_state_obs_test))
        mean_relative_error_state_forward_problem(relative_error(batch_state_pred_test_forward_problem, batch_state_obs_test))
        mean_relative_error_parameter(relative_error(batch_parameter_pred_test, batch_parameter_test))
        
###############################################################################
#                             Train Neural Network                            #
############################################################################### 
    print('Beginning Training')
    for epoch in range(hyperp.num_epochs):
        print('================================')
        print('            Epoch %d            ' %(epoch))
        print('================================')
        print(file_paths.filename)
        print('GPU: ' + run_options.which_gpu + '\n')
        print('Optimizing %d batches of size %d:' %(num_batches_train, hyperp.batch_size))
        start_time_epoch = time.time()
        for batch_num, (batch_parameter_train, batch_state_obs_train) in parameter_and_state_obs_train.enumerate():
            start_time_batch = time.time()
            gradients = train_step(batch_parameter_train, batch_state_obs_train)
            elapsed_time_batch = time.time() - start_time_batch
            #=== Display Model Summary ===#
            if batch_num == 0 and epoch == 0:
                NN.summary()
            if batch_num  == 0:
                print('Time per Batch: %.4f' %(elapsed_time_batch))
        
        #=== Computing Relative Errors Validation ===#
        for batch_parameter_val, batch_state_obs_val in parameter_and_state_obs_val:
            val_step(batch_parameter_val, batch_state_obs_val)
            
        #=== Computing Relative Errors Test ===#
        for batch_parameter_test, batch_state_obs_test in parameter_and_state_obs_test:
            test_step(batch_parameter_test, batch_state_obs_test)

        #=== Track Training Metrics, Weights and Gradients ===#
        with summary_writer.as_default():
            tf.summary.scalar('loss_training', mean_loss_train.result(), step=epoch)
            tf.summary.scalar('loss_training_autoencoder', mean_loss_train_autoencoder.result(), step=epoch)
            tf.summary.scalar('loss_training_model_augmented', mean_loss_train_model_augmented.result(), step=epoch)
            tf.summary.scalar('loss_val', mean_loss_val.result(), step=epoch)
            tf.summary.scalar('loss_val_autoencoder', mean_loss_val_autoencoder.result(), step=epoch)
            tf.summary.scalar('loss_val_model_augmented', mean_loss_val_model_augmented.result(), step=epoch)
            tf.summary.scalar('loss_test', mean_loss_test.result(), step=epoch)
            tf.summary.scalar('loss_test_autoencoder', mean_loss_test_autoencoder.result(), step=epoch)
            tf.summary.scalar('loss_test_model_augmented', mean_loss_test_model_augmented.result(), step=epoch)
            tf.summary.scalar('relative_error_parameter_autoencoder', mean_relative_error_state_autoencoder.result(), step=epoch)
            tf.summary.scalar('relative_error_parameter_model_augmented', mean_relative_error_state_forward_problem.result(), step=epoch)
            tf.summary.scalar('relative_error_state_obs', mean_relative_error_parameter.result(), step=epoch)
            for w in NN.weights:
                tf.summary.histogram(w.name, w, step=epoch)
            l2_norm = lambda t: tf.sqrt(tf.reduce_sum(tf.pow(t, 2)))
            for gradient, variable in zip(gradients, NN.trainable_variables):
                tf.summary.histogram("gradients_norm/" + variable.name, l2_norm(gradient), step = epoch)              
                
        #=== Update Storage Arrays ===#
        storage_array_loss_train = np.append(storage_array_loss_train, mean_loss_train.result())
        storage_array_loss_train_autoencoder = np.append(storage_array_loss_train_autoencoder, mean_loss_train_autoencoder.result())
        storage_array_loss_train_model_augmented = np.append(storage_array_loss_train_model_augmented, mean_loss_train_model_augmented.result())
        storage_array_loss_val = np.append(storage_array_loss_val, mean_loss_val.result())
        storage_array_loss_val_autoencoder = np.append(storage_array_loss_val_autoencoder, mean_loss_val_autoencoder.result())
        storage_array_loss_val_model_augmented = np.append(storage_array_loss_val_model_augmented, mean_loss_val_model_augmented.result())
        storage_array_loss_test = np.append(storage_array_loss_test, mean_loss_test.result())
        storage_array_loss_test_autoencoder = np.append(storage_array_loss_test_autoencoder, mean_loss_test_autoencoder.result())
        storage_array_loss_test_model_augmented = np.append(storage_array_loss_test_model_augmented, mean_loss_test_model_augmented.result())
        storage_array_relative_error_state_autoencoder = np.append(storage_array_relative_error_state_autoencoder, mean_relative_error_state_autoencoder.result())
        storage_array_relative_error_state_forward_problem = np.append(storage_array_relative_error_state_forward_problem, mean_relative_error_state_forward_problem.result())
        storage_array_relative_error_parameter = np.append(storage_array_relative_error_parameter, mean_relative_error_parameter.result())
            
        #=== Display Epoch Iteration Information ===#
        elapsed_time_epoch = time.time() - start_time_epoch
        print('Time per Epoch: %.4f\n' %(elapsed_time_epoch))
        print('Train Loss: Full: %.3e, State: %.3e, Parameter: %.3e' %(mean_loss_train.result(), mean_loss_train_autoencoder.result(), mean_loss_train_model_augmented.result()))
        print('Val Loss: Full: %.3e, State: %.3e, Parameter: %.3e' %(mean_loss_val.result(), mean_loss_val_autoencoder.result(), mean_loss_val_model_augmented.result()))
        print('Test Loss: Full: %.3e, State: %.3e, Parameter: %.3e' %(mean_loss_test.result(), mean_loss_test_autoencoder.result(), mean_loss_test_model_augmented.result()))
        print('Rel Errors: AE: %.3e, Forward: %.3e, Inverse: %.3e\n' %(mean_relative_error_state_autoencoder.result(), mean_relative_error_state_forward_problem.result(), mean_relative_error_parameter.result()))
        start_time_epoch = time.time()
        
        #=== Resetting Metrics ===#
        mean_loss_train.reset_states()
        mean_loss_train_autoencoder.reset_states()
        mean_loss_train_model_augmented.reset_states()
        mean_loss_val.reset_states()
        mean_loss_val_autoencoder.reset_states()
        mean_loss_val_model_augmented.reset_states()    
        mean_loss_test.reset_states()
        mean_loss_test_autoencoder.reset_states()
        mean_loss_test_model_augmented.reset_states()
        mean_relative_error_state_autoencoder.reset_states()
        mean_relative_error_state_forward_problem.reset_states()
        mean_relative_error_parameter.reset_states()
            
    #=== Save Final Model ===#
    NN.save_weights(file_paths.NN_savefile_name)
    print('Final Model Saved') 
    
    return storage_array_loss_train, storage_array_loss_train_autoencoder, storage_array_loss_train_model_augmented, storage_array_loss_val, storage_array_loss_val_autoencoder, storage_array_loss_val_model_augmented, storage_array_loss_test, storage_array_loss_test_autoencoder, storage_array_loss_test_model_augmented, storage_array_relative_error_state_autoencoder, storage_array_relative_error_state_forward_problem, storage_array_relative_error_parameter 