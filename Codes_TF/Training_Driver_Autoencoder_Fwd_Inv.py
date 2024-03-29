#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Sep 14 14:35:58 2019

@author: Hwan Goh
"""

import tensorflow as tf # for some reason this must be first! Or else I get segmentation fault
tf.reset_default_graph()
tf.logging.set_verbosity(tf.logging.FATAL) # Suppresses all the messages when run begins
import numpy as np
import pandas as pd

from NN_Autoencoder_Fwd_Inv import AutoencoderFwdInv

import pdb #Equivalent of keyboard in MATLAB, just add "pdb.set_trace()"

import os
import sys
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['OMP_NUM_THREADS'] = '6'
sys.path.insert(0, '../../Utilities/')

np.random.seed(1234)

###############################################################################
#                       Hyperparameters and Filenames                         #
###############################################################################
class HyperParameters:
    data_type         = 'full'
    num_hidden_layers = 1
    truncation_layer  = 1 # Indexing includes input and output layer with input layer indexed by 0
    num_hidden_nodes  = 1446
    penalty           = 1
    num_training_data = 20
    batch_size        = 2
    num_epochs        = 2000
    gpu               = '1'
    
class RunOptions:
    def __init__(self, hyper_p): 
        #=== Use LBFGS Optimizer ===#
        self.use_LBFGS = 0
        
        #=== Data type ===#
        self.use_full_domain_data = 0
        self.use_bnd_data = 0
        self.use_bnd_data_only = 0
        if hyper_p.data_type == 'full':
            self.use_full_domain_data = 1
        if hyper_p.data_type == 'bnd':
            self.use_bnd_data = 1
        if hyper_p.data_type == 'bndonly':
            self.use_bnd_data_only = 1
        
        #===  Observation Dimensions === #
        self.full_domain_dimensions = 1446 
        if self.use_full_domain_data == 1:
            self.state_obs_dimensions = self.full_domain_dimensions 
        if self.use_bnd_data == 1 or self.use_bnd_data_only == 1:
            self.state_obs_dimensions = 614
        
        #===  Other options ===#
        self.num_testing_data = 20
        
        #===  File name ===#
        if hyper_p.penalty >= 1:
            hyper_p.penalty = int(hyper_p.penalty)
            penalty_string = str(hyper_p.penalty)
        else:
            penalty_string = str(hyper_p.penalty)
            penalty_string = 'pt' + penalty_string[2:]

        self.filename = hyper_p.data_type + '_hl%d_tl%d_hn%d_p%s_d%d_b%d_e%d' %(hyper_p.num_hidden_layers, hyper_p.truncation_layer, hyper_p.num_hidden_nodes, penalty_string, hyper_p.num_training_data, hyper_p.batch_size, hyper_p.num_epochs)

        #=== Loading and saving data ===#
        if self.use_full_domain_data == 1:
            self.observation_indices_savefilepath = '../Data/' + 'thermal_fin_full_domain'
            self.parameter_train_savefilepath = '../Data/' + 'parameter_train_%d' %(hyper_p.num_training_data) 
            self.state_obs_train_savefilepath = '../Data/' + 'state_train_%d' %(hyper_p.num_training_data) 
            self.parameter_test_savefilepath = '../Data/' + 'parameter_test_%d' %(self.num_testing_data) 
            self.state_obs_test_savefilepath = '../Data/' + 'state_test_%d' %(self.num_testing_data) 
        if self.use_bnd_data == 1 or self.use_bnd_data_only == 1:
            self.observation_indices_savefilepath = '../Data/' + 'thermal_fin_bnd_indices'
            self.parameter_train_savefilepath = '../Data/' + 'parameter_train_bnd_%d' %(hyper_p.num_training_data) 
            self.state_obs_train_savefilepath = '../Data/' + 'state_train_bnd_%d' %(hyper_p.num_training_data) 
            self.parameter_test_savefilepath = '../Data/' + 'parameter_test_bnd_%d' %(self.num_testing_data) 
            self.state_obs_test_savefilepath = '../Data/' + 'state_test_bnd_%d' %(self.num_testing_data)             
        
        #=== Saving neural network ===#
        self.NN_savefile_directory = '../Trained_NNs/' + self.filename # Since we need to save four different types of files to save a neural network model, we need to create a new folder for each model
        self.NN_savefile_name = self.NN_savefile_directory + '/' + self.filename # The file path and name for the four files

        #=== Creating Directories ===#
        if not os.path.exists(self.NN_savefile_directory):
            os.makedirs(self.NN_savefile_directory)

###############################################################################
#                                 Training                                    #
###############################################################################
def trainer(hyper_p, run_options):
        
    hyper_p.batch_size = hyper_p.num_training_data
    
    #=== Load observation indices ===# 
    print('Loading Boundary Indices')
    df_obs_indices = pd.read_csv(run_options.observation_indices_savefilepath + '.csv')    
    obs_indices = df_obs_indices.to_numpy()    
    #=== Load Train and Test Data ===#  
    print('Loading Training Data')
    df_parameter_train = pd.read_csv(run_options.parameter_train_savefilepath + '.csv')
    df_state_obs_train = pd.read_csv(run_options.state_obs_train_savefilepath + '.csv')
    parameter_train = df_parameter_train.to_numpy()
    state_obs_train = df_state_obs_train.to_numpy()
    parameter_train = parameter_train.reshape((hyper_p.num_training_data, 9))
    state_obs_train = state_obs_train.reshape((hyper_p.num_training_data, run_options.state_obs_dimensions))
    print('Loading Testing Data')
    df_parameter_test = pd.read_csv(run_options.parameter_test_savefilepath + '.csv')
    df_state_obs_test = pd.read_csv(run_options.state_obs_test_savefilepath + '.csv')
    parameter_test = df_parameter_test.to_numpy()
    state_obs_test = df_state_obs_test.to_numpy()
    parameter_test = parameter_test.reshape((run_options.num_testing_data, 9))
    state_obs_test = state_obs_test.reshape((run_options.num_testing_data, run_options.state_obs_dimensions))
      
    #=== Neural network ===#
    NN = AutoencoderFwdInv(hyper_p, run_options, parameter_train.shape[1], run_options.full_domain_dimensions, obs_indices, run_options.NN_savefile_name, construct_flag = 1)
    
    
###############################################################################
#                                 Driver                                      #
###############################################################################     
if __name__ == "__main__":     

    #=== Hyperparameters ===#    
    hyper_p = HyperParameters()
    
    if len(sys.argv) > 1:
            hyper_p.data_type         = str(sys.argv[1])
            hyper_p.num_hidden_layers = int(sys.argv[2])
            hyper_p.truncation_layer  = int(sys.argv[3])
            hyper_p.num_hidden_nodes  = int(sys.argv[4])
            hyper_p.penalty           = float(sys.argv[5])
            hyper_p.num_training_data = int(sys.argv[6])
            hyper_p.batch_size        = int(sys.argv[7])
            hyper_p.num_epochs        = int(sys.argv[8])
            hyper_p.gpu               = str(sys.argv[9])
            
    #=== Set run options ===#         
    run_options = RunOptions(hyper_p)
    
    #=== Initiate training ===#
    trainer(hyper_p, run_options) 
    
     
     
     
     
     
     
     
     
     
     
     
     