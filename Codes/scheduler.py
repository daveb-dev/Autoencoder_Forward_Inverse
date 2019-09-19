#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep 18 20:53:06 2019

@author: Jon Wittmer
"""

from Training_Driver_Autoencoder_Fwd_Inv import RunOptions
import nvidia_smi
import copy
import subprocess
import os
from mpi4py import MPI
from time import sleep
import pdb #Equivalent of keyboard in MATLAB, just add "pdb.set_trace()"

class FLAGS:
    RECEIVED = 1
    RUN_FINISHED = 2
    EXIT = 3
    NEW_RUN = 4

###############################################################################
#                        Generate List of Scenarios                           #
###############################################################################
def get_scenarios_list(hyper_p):
    hyper_p_list = [hyper_p.num_hidden_layers, hyper_p.truncation_layer,  hyper_p.num_hidden_nodes, \
                    hyper_p.penalty, hyper_p.num_training_data, hyper_p.batch_size, hyper_p.num_epochs]
    
    scenarios_list = assemble_parameters(hyper_p_list)
        
    scenarios = []
    for vals in scenarios_list:
        p                   = RunOptions()
        p.num_hidden_layers = vals[0]
        p.truncation_layer  = vals[1]
        p.num_hidden_nodes  = vals[2]
        p.penalty           = vals[3]
        p.num_training_data = vals[4]
        p.batch_size        = vals[5]
        p.num_epochs        = vals[6]
        
        p.N_u    = vals[0]
        p.N_f    = vals[1]
        p.rho    = vals[2]
        p.epochs = vals[3]
        scenarios.append(copy.deepcopy(p))

    return scenarios

def assemble_parameters(hyper_p_list):
    # params is a list of lists, with each inner list representing
    # a different model parameter. This function constructs the combinations
    return get_combinations(hyper_p_list[0], hyper_p_list[1:])
    
def get_combinations(hyper_p, hyper_p_list):
    # assign here in case this is the last list item
    combos = hyper_p_list[0]
    
    # reassign when it is not the last item - recursive algorithm
    if len(hyper_p_list) > 1:
        combos = get_combinations(hyper_p_list[0], hyper_p_list[1:])
        
    # concatenate the output into a list of lists
    output = []
    for i in hyper_p:
        for j in combos:
            # convert to list if not already
            j = j if isinstance(j, list) else [j]            
            # for some reason, this needs broken into 3 lines...Python
            temp = [i]
            temp.extend(j)
            output.append(temp)
    return output                

###############################################################################
#                            Schedule and Run                                 #
###############################################################################
def schedule_runs(scenarios, nproc, comm, total_gpus = 4):
    scenarios_left = len(scenarios)
    print(str(scenarios_left) + ' total runs')
    
    # initialize available processes
    available_processes = list(range(1, nprocs))
    
    flags = FLAGS()
    
    # start running tasks
    while scenarios_left > 0:
        
        # check for returning processes
        s = MPI.Status()
        comm.Iprobe(status=s)
        if s.tag == flags.RUN_FINISHED:
            print('Run ended. Starting new thread.')
            data = comm.recv()
            scenarios_left -= 1
            if len(scenarios) == 0:
                comm.send([], s.source, flags.EXIT)
            else: 
                available_processes.append(s.source)

        # assign training to process
        available_gpus = available_GPUs(total_gpus)
        print(available_gpus)
        print(available_processes)

        if len(available_gpus) > 0 and len(available_processes) > 0 and len(scenarios) > 0:
            curr_process = available_processes.pop(0)
            curr_scenario = scenarios.pop(0)
            curr_scenario.gpu = str(available_gpus.pop(0))
            
            print('Beginning Training of NN:')
            print_scenario(curr_scenario)
            print()
            
            # block here to make sure the process starts before moving on so we don't overwrite buffer
            print('current process: ' + str(curr_process))
            req = comm.isend(curr_scenario, curr_process, flags.NEW_RUN)
            req.wait()
            
        elif len(available_processes) > 0 and len(scenarios) == 0:
            while len(available_processes) > 0:
                proc = available_processes.pop(0)
                comm.send([], proc, flags.EXIT)

        sleep(30)           
    
def available_GPUs(total_gpus):
    available = []
    for i in range(total_gpus):
        handle  = nvidia_smi.nvmlDeviceGetHandleByIndex(i)
        res     = nvidia_smi.nvmlDeviceGetUtilizationRates(handle)
        mem_res = nvidia_smi.nvmlDeviceGetMemoryInfo(handle)
        if res.gpu < 30 and (mem_res.used / mem_res.total *100) < 30:
            available.append(i)
    return available 

def print_scenario(p):
    print()
    print(f'    p.num_hidden_layers:   {p.num_hidden_layers}')
    print(f'    p.truncation_layer:    {p.truncation_layer}')
    print(f'    p.penalty:             {p.penalty}')
    print(f'    p.num_training_data:   {p.num_training_data}')
    print(f'    p.batch_size:          {p.batch_size}')
    print(f'    p.num_epochs:          {p.num_epochs}')
    print()

###############################################################################
#                                   Executor                                  #
###############################################################################
if __name__ == '__main__':
    
    # mpi stuff
    comm   = MPI.COMM_WORLD
    nprocs = comm.Get_size()
    rank   = comm.Get_rank()

    if rank == 0:
        
        #########################
        #   Get Scenarios List  #
        #########################   
        hyper_p = RunOptions()
            
        hyper_p.num_hidden_layers = [1, 3, 5]
        hyper_p.truncation_layer = [2, 3, 4] # Indexing includes input and output layer
        hyper_p.num_hidden_nodes = [200]
        hyper_p.penalty = [10, 20, 30, 40]
        hyper_p.num_training_data = [5000, 10000]
        hyper_p.batch_size = [5000, 10000]
        hyper_p.num_epochs = [50000]
        
        scenarios = get_scenarios_list(hyper_p)
        
        schedule_runs(scenarios, nprocs, comm)
    
    else:
        while True:
            status = MPI.Status()
            data = comm.recv(source=0, status=status)
            
            if status.tag == FLAGS.EXIT:
                break
            
            proc = subprocess.Popen(['./Abgrall_ADMM.py', f'{data.N_u}', f'{data.N_f}', f'{data.rho}', f'{int(data.epochs)}', f'{data.gpu}'])
            proc.wait()
            
            req = comm.isend([], 0, FLAGS.RUN_FINISHED)
            req.wait()