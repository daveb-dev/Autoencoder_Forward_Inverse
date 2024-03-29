#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Sep 15 15:34:49 2019

@author: hwan
"""
import sys

import tensorflow as tf
from Utilities.get_thermal_fin_data import load_thermal_fin_test_data
from Utilities.NN_Autoencoder_Fwd_Inv import AutoencoderFwdInv
from Utilities.predict_and_save import predict_and_save

import pdb #Equivalent of keyboard in MATLAB, just add "pdb.set_trace()"


###############################################################################
#                       Hyperparameters and Run_Options                       #
###############################################################################
class Hyperparameters:
    data_type         = 'full'
    num_hidden_layers = 5
    truncation_layer  = 3 # Indexing includes input and output layer with input layer indexed by 0
    num_hidden_nodes  = 500
    activation        = 'relu'
    penalty           = 1
    penalty_aug       = 1
    batch_size        = 1000
    num_epochs        = 1000
    
class RunOptions:
    def __init__(self): 
        #=== Autoencoder Type ===#
        self.use_standard_autoencoder = 1
        self.use_reverse_autoencoder = 0
        
        #=== Autoencoder Loss ===#
        self.use_model_aware = 1
        self.use_model_augmented = 0
        self.use_model_induced = 0
        
        #=== Data Set ===#
        self.data_thermal_fin_nine = 0
        self.data_thermal_fin_vary = 1
        
        #=== Data Set Size ===#
        self.num_data_train = 50000
        self.num_data_test = 200
        
        #=== Data Dimensions ===#
        self.fin_dimensions_2D = 0
        self.fin_dimensions_3D = 1
        
        #=== Random Seed ===#
        self.random_seed = 1234

        #=== Parameter and Observation Dimensions === #
        if self.fin_dimensions_2D == 1:
            self.full_domain_dimensions = 1446 
        if self.fin_dimensions_3D == 1:
            self.full_domain_dimensions = 4090 
        if self.data_thermal_fin_nine == 1:
            self.parameter_dimensions = 9
        if self.data_thermal_fin_vary == 1:
            self.parameter_dimensions = self.full_domain_dimensions

###############################################################################
#                                 File Paths                                  #
###############################################################################  
class FilePaths():              
    def __init__(self, hyperp, run_options): 
        #=== Declaring File Name Components ===#
        if run_options.use_standard_autoencoder == 1:
            self.autoencoder_type = ''
        if run_options.use_reverse_autoencoder == 1:
            self.autoencoder_type = 'rev_'
        if run_options.use_model_aware == 1:
            self.autoencoder_loss = ''
        if run_options.use_model_augmented == 1:
            self.autoencoder_loss = 'maug'
        if run_options.use_model_induced == 1:
            self.autoencoder_loss = 'mind'
        if run_options.data_thermal_fin_nine == 1:
            self.dataset = 'thermalfin9'
            parameter_type = '_nine'
        if run_options.data_thermal_fin_vary == 1:
            self.dataset = 'thermalfinvary'
            parameter_type = '_vary'
        if run_options.fin_dimensions_2D == 1:
            fin_dimension = ''
        if run_options.fin_dimensions_3D == 1:
            fin_dimension = '_3D'
        if hyperp.penalty >= 1:
            hyperp.penalty = int(hyperp.penalty)
            penalty_string = str(hyperp.penalty)
        else:
            penalty_string = str(hyperp.penalty)
            penalty_string = 'pt' + penalty_string[2:]
        if hyperp.penalty_aug >= 1:
            hyperp.penalty_aug = int(hyperp.penalty_aug)
            penalty_string_aug = str(hyperp.penalty_aug)
        else:
            penalty_string_aug = str(hyperp.penalty_aug)
            penalty_string_aug = 'pt' + penalty_string_aug[2:]    
 
        #=== File Name ===#
        if run_options.use_model_aware == 1:
            self.filename = self.autoencoder_type + self.autoencoder_loss + self.dataset + '_' + hyperp.data_type + fin_dimension + '_hl%d_tl%d_hn%d_%s_p%s_d%d_b%d_e%d' %(hyperp.num_hidden_layers, hyperp.truncation_layer, hyperp.num_hidden_nodes, hyperp.activation, penalty_string, run_options.num_data_train, hyperp.batch_size, hyperp.num_epochs)
        if run_options.use_model_augmented == 1:
            self.filename = self.autoencoder_type + self.autoencoder_loss + '_' + self.dataset + '_' + hyperp.data_type + fin_dimension + '_hl%d_tl%d_hn%d_%s_p%s_d%d_b%d_e%d' %(hyperp.num_hidden_layers, hyperp.truncation_layer, hyperp.num_hidden_nodes, hyperp.activation, penalty_string, run_options.num_data_train, hyperp.batch_size, hyperp.num_epochs)
        if run_options.use_model_induced == 1:
            self.filename = self.autoencoder_type + self.autoencoder_loss + '_' + self.dataset + '_' + hyperp.data_type + fin_dimension + '_hl%d_tl%d_hn%d_%s_p%s_paug%s_d%d_b%d_e%d' %(hyperp.num_hidden_layers, hyperp.truncation_layer, hyperp.num_hidden_nodes, hyperp.activation, penalty_string, penalty_string_aug, run_options.num_data_train, hyperp.batch_size, hyperp.num_epochs)

        #=== Loading and Saving Data ===#
        self.observation_indices_savefilepath = '../../Datasets/Thermal_Fin/' + 'obs_indices' + '_' + hyperp.data_type + fin_dimension
        self.parameter_train_savefilepath = '../../Datasets/Thermal_Fin/' + 'parameter_train_%d' %(run_options.num_data_train) + fin_dimension + parameter_type
        self.state_obs_train_savefilepath = '../../Datasets/Thermal_Fin/' + 'state_train_%d' %(run_options.num_data_train) + fin_dimension + '_' + hyperp.data_type + parameter_type
        self.parameter_test_savefilepath = '../../Datasets/Thermal_Fin/' + 'parameter_test_%d' %(run_options.num_data_test) + fin_dimension + parameter_type 
        self.state_obs_test_savefilepath = '../../Datasets/Thermal_Fin/' + 'state_test_%d' %(run_options.num_data_test) + fin_dimension + '_' + hyperp.data_type + parameter_type
        
        #=== Save File Directory ===#
        self.NN_savefile_directory = '../Trained_NNs/' + self.filename
        self.NN_savefile_name = self.NN_savefile_directory + '/' + self.filename
        
        #=== File Path for Loading One Instance of Test Data ===#
        self.loadfile_name_parameter_test = '../../Datasets/Thermal_Fin/' + '/parameter_test' + fin_dimension + parameter_type
        self.loadfile_name_state_test = '../../Datasets/Thermal_Fin/' + '/state_test' + fin_dimension + parameter_type
       
        #=== Save File Path for Predictions ===#
        self.savefile_name_parameter_test = self.NN_savefile_directory + '/' + 'parameter_test' + fin_dimension + parameter_type
        self.savefile_name_state_test = self.NN_savefile_directory + '/' + 'state_test' + fin_dimension + parameter_type
        self.savefile_name_parameter_pred = self.NN_savefile_name + '_parameter_pred'
        self.savefile_name_state_pred = self.NN_savefile_name + '_state_pred'     

###############################################################################
#                 Load Testing Data and Trained Neural Network                #
###############################################################################
def load_predict_save(hyperp, run_options, file_paths): 
    #=== Load Testing Data ===# 
    obs_indices, parameter_test, state_obs_test, data_input_shape, parameter_dimension\
    = load_thermal_fin_test_data(file_paths, run_options.num_data_test, run_options.parameter_dimensions) 

    #=== Shuffling Data and Forming Batches ===#
    parameter_and_state_obs_test = tf.data.Dataset.from_tensor_slices((parameter_test, state_obs_test)).shuffle(8192, seed=run_options.random_seed).batch(hyperp.batch_size)

    #=== Data and Latent Dimensions of Autoencoder ===#    
    if run_options.use_standard_autoencoder == 1:
        data_dimension = parameter_dimension
        if hyperp.data_type == 'full':
            latent_dimension = run_options.full_domain_dimensions
        if hyperp.data_type == 'bnd':
            latent_dimension = len(obs_indices)
    
    if run_options.use_reverse_autoencoder == 1:
        if hyperp.data_type == 'full':
            data_dimension = run_options.full_domain_dimensions
        if hyperp.data_type == 'bnd':
            data_dimension = len(obs_indices)
        latent_dimension = parameter_dimension
        
    #=== Load Trained Neural Network ===#
    NN = AutoencoderFwdInv(hyperp, data_dimension, latent_dimension)
    NN.load_weights(file_paths.NN_savefile_name)  
    
    #=== Predict and Save ===#
    predict_and_save(hyperp, run_options, file_paths, NN, parameter_and_state_obs_test, obs_indices)

###############################################################################
#                                    Driver                                   #
###############################################################################
if __name__ == "__main__":
    
    #=== Hyperparameters and Run Options ===#    
    hyperp = Hyperparameters()
    run_options = RunOptions()
    
    if len(sys.argv) > 1:
        hyperp.data_type         = str(sys.argv[1])
        hyperp.num_hidden_layers = int(sys.argv[2])
        hyperp.truncation_layer  = int(sys.argv[3])
        hyperp.num_hidden_nodes  = int(sys.argv[4])
        hyperp.activation        = str(sys.argv[5])
        hyperp.penalty           = float(sys.argv[6])
        hyperp.penalty_aug       = float(sys.argv[7])
        hyperp.batch_size        = int(sys.argv[8])
        hyperp.num_epochs        = int(sys.argv[9])

    #=== File Names ===#
    file_paths = FilePaths(hyperp, run_options)
    
    #=== Predict and Save ===#
    load_predict_save(hyperp, run_options, file_paths)
    
