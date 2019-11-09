#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep 18 20:53:06 2019

@author: Jon Wittmer
"""

import subprocess
import copy
from Utilities.get_hyperparameter_permutations import get_hyperparameter_permutations
from Training_Driver_Autoencoder_Fwd_Inv import HyperParameters
import pdb #Equivalent of keyboard in MATLAB, just add "pdb.set_trace()"

class FLAGS:
    RECEIVED = 1
    RUN_FINISHED = 2
    EXIT = 3
    NEW_RUN = 4

###############################################################################
#                                   Executor                                  #
###############################################################################
if __name__ == '__main__':
                            
    #########################
    #   Get Scenarios List  #
    #########################   
    hyper_p = HyperParameters() # Assign instance attributes below, DO NOT assign an instance attribute to GPU
    
    # assign instance attributes for hyper_p
    hyper_p.data_type         = ['full']
    hyper_p.num_hidden_layers = [3]
    hyper_p.truncation_layer  = [2] # Indexing includes input and output layer with input layer indexed by 0
    hyper_p.num_hidden_nodes  = [200, 500, 1000]
    hyper_p.penalty           = [0.01, 1, 5, 10]
    hyper_p.num_training_data = [50000]
    hyper_p.batch_size        = [1000]
    hyper_p.num_epochs        = [4000]
    
    permutations_list, hyper_p_keys = get_hyperparameter_permutations(hyper_p) 
    print('permutations_list generated')
    
    # Convert each list in permutations_list into class attributes
    scenarios_class_instances = []
    for scenario_values in permutations_list: 
        hyper_p_scenario = HyperParameters()
        for i in range(0, len(scenario_values)):
            setattr(hyper_p_scenario, hyper_p_keys[i], scenario_values[i])
        scenarios_class_instances.append(copy.deepcopy(hyper_p_scenario))
    
    for scenario in scenarios_class_instances:
        subprocess.Popen(['./Training_Driver_Autoencoder_Fwd_Inv.py', f'{scenario.data_type}', f'{scenario.num_hidden_layers}', f'{scenario.truncation_layer}', f'{scenario.num_hidden_nodes}', f'{scenario.penalty:.2f}', f'{scenario.num_training_data}', f'{scenario.batch_size}', f'{scenario.num_epochs}',  f'{scenario.gpu}'])
                
    print('All scenarios computed')