# Hyperparameter Search on Slurm


This repo provides code for easily launching jobs on Slurm systems. It supports Grid Search and Random Search.

In order to use this pakage, the user must specify two files: a config file containing parameters, and a run script.

### Config file

This is a yaml file containing hyper-parameters, sbatch flags, and a other options. It has the following format:

```yaml
logdir: path/to/logdir # required
prefix: exp_name_prefix # optional. default: exp
njobs: 2 # number of slurm jobs to launch for each experiment. required
algorithm: random # or grid. required
nexps: 10 # number of experiments to laucnh when using random search.

# Hyperparameters. Parameter values can be specified with the "values" and "range" keywords.
# When using grid search, all parameters must have the "values" keyword or be constant.
# When using random search, parameters will be sampled uniformly from "range" if specified else "values".
# When using the "range" keyword, you can specify a scale to sample in (linear or log). 
# Parameters can be assigned to groups for grid search. The values of the grouped parameters
# will be iterated over as if they were a single parameter.
params: 
    p1: 5 # consntant
    p2:
        values: [1,2,3,4,5]
    namespace1:
        p3:
            range: [1, 10]
            scale: linear
        p4:
            range: [1, 100] # will sample from "range" when using random search,
                            # and iterate over "values" when using grid search.
            values: [1, 100]
            scale: log
    
    p5:
        values: [1,3,5]
        group: 0
    
    p6:
        values: [0,2,4]
        group: 0  # For grid search, p6 will have value 0 when p5 has value 1,
                  # 2 when p5 has value 3, and so on.

# Define sbatch flags here.
# The "d", "J", and "o" flags are used by this package and shouldn't be defined here.
slurm:
    p: contrib-cpu
    c: 2
    C: avx&highmem
```

### Run script

The run script should run the user's code with the specified parameters. It has the following interface:

```bash
./run_script params.yaml
```

The "params.yaml" file has the following format:

```yaml
logdir: path/to/logdir/exp_name_prefix0

p1: 5
p2: 5
namespace1:
  p3: 5.655377361451643
  p4: 14.188903177147603
p5: 1
p6: 0
```


## Pakage Interface

Once installed, the pakage has three functions: "launch", "add_jobs", and "copy_exp".

### launch command

```bash
python -m slurm.launch config.yaml run_script
```

This command will set up the log directory and launch slurm jobs using sbatch.

### add_jobs command

```bash
python -m slurm.add_jobs path/to/logdir -n num_jobs -e exp0 exp1
```

This command launches additional slurm jobs using sbatch for the specified experiments in a log directory. If the "-e" flag is unused, all experiments will be extended.

### copy_exp command

```bash
python -m slurm.copy_exp path/to/logdir expname newexpname -l newlogdir
```

This command clones an experiment directory under a new name and creates the necessary files so that the new experiment can be run with the add_jobs command. The "-l" flag optionally allows the user to copy the experiment to a new log directory.


## Installation

This package can be installed by cloning the github reqopsitory, and then installing with pip:

```bash
pip install -e /path/to/repository
```
