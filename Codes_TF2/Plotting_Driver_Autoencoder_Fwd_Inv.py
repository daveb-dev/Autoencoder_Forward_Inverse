#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Nov 10 12:18:38 2019

@author: hwan
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov  6 12:59:59 2019

@author: hwan
"""
import sys
import os

from Utilities.plot_and_save import plot_and_save

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
    penalty           = 50
    batch_size        = 1000
    num_epochs        = 500
    
class RunOptions:
    def __init__(self): 
        #=== Data Set ===#
        self.data_thermal_fin_nine = 0
        self.data_thermal_fin_vary = 1
        
        #=== Data Set Size ===#
        self.num_data_train = 50000
        self.num_data_test = 200
        
        #=== Data Dimensions ===#
        self.fin_dimensions_2D = 1
        self.fin_dimensions_3D = 0
        
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
#                                 File Name                                   #
###############################################################################                
class FilePaths():              
    def __init__(self, hyperp, run_options): 
        #=== Declaring File Name Components ===#
        if run_options.data_thermal_fin_nine == 1:
            self.dataset = 'thermalfin9'
        if run_options.data_thermal_fin_vary == 1:
            self.dataset = 'thermalfinvary'
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
            
        #=== File Name ===#
        self.filename = self.dataset + '_' + hyperp.data_type + fin_dimension + '_hl%d_tl%d_hn%d_%s_p%s_d%d_b%d_e%d' %(hyperp.num_hidden_layers, hyperp.truncation_layer, hyperp.num_hidden_nodes, hyperp.activation, penalty_string, run_options.num_data_train, hyperp.batch_size, hyperp.num_epochs)
       
        #=== Save File Directory ===#
        self.NN_savefile_directory = '../Trained_NNs/' + self.filename
        self.NN_savefile_name = self.NN_savefile_directory + '/' + self.filename
  
        #=== Save File Path ===#
        self.observation_indices_savefilepath = '../../Datasets/Thermal_Fin/' + 'obs_indices' + '_' + hyperp.data_type + fin_dimension
    
        #=== Save File Path for One Instance of Test Data ===#
        self.savefile_name_parameter_test = self.NN_savefile_directory + '/parameter_test' + fin_dimension
        if hyperp.data_type == 'full':
            self.savefile_name_state_test = self.NN_savefile_directory + '/state_test' + fin_dimension
        if hyperp.data_type == 'bndonly':
            self.savefile_name_state_test = self.NN_savefile_directory + '/state_test_bnd' + fin_dimension           
            
        #=== Loading Predictions ===#    
        self.savefile_name_parameter_pred = self.NN_savefile_name + '_parameter_pred' + fin_dimension
        self.savefile_name_state_pred = self.NN_savefile_name + '_state_pred' + fin_dimension
            
        #=== Savefile Path for Figures ===#    
        self.figures_savefile_directory = '../Figures/' + self.filename
        self.figures_savefile_name = self.figures_savefile_directory + '/' + self.filename
        self.figures_savefile_name_parameter_test = self.figures_savefile_directory + '/' + 'parameter_test' + fin_dimension
        self.figures_savefile_name_state_test = self.figures_savefile_directory + '/' + 'state_test' + fin_dimension
        self.figures_savefile_name_parameter_pred = self.figures_savefile_name + '_parameter_pred' + fin_dimension
        self.figures_savefile_name_state_pred = self.figures_savefile_name + '_state_pred' + fin_dimension
        
        #=== Creating Directories ===#
        if not os.path.exists(self.figures_savefile_directory):
            os.makedirs(self.figures_savefile_directory)

###############################################################################
#                                  Driver                                     #
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
        hyperp.penalty           = float(sys.argv[5])
        hyperp.batch_size        = int(sys.argv[6])
        hyperp.num_epochs        = int(sys.argv[7])

    #=== File Names ===#
    file_paths = FilePaths(hyperp, run_options)
    
    #=== Plot and Save ===#
    plot_and_save(hyperp, run_options, file_paths)
    



    
    
    
    
    
    