import os, sys, argparse, time, yaml
from subprocess import call
from shutil import copyfile
import numpy as np


def main(logdir, njobs, exps):
    logdir = os.path.abspath(path)

    if len(exps) == 0:
        configs = os.path.listdir(os.path.join(logdir, '.configs'))
    else:
        configs = [os.path.join(logdir, '.configs', f'{e}.yaml') for e in exps]

    with open(os.path.join(logdir, '.config'), 'r') as f:
        c = yaml.load(f)


    id = abs(hash(os.path.abspath(c['logdir'])))
    cmd = f'sbatch -d singleton -J exp{i}_{id}'
    for flag, value in c['slurm'].items():
        cmd += f' --{flag} {value}' if len(flag) > 1 else f' -{flag} {value}'
    for _ in range(njobs):
        outfile = os.path.join(c['logdir'], f'.slurm/exp{i}_%j.out')
        call(cmd.split() + ['-o', outfile, exp_launch])






if __name__=='__main__':
    parser = argparse.ArgumentParser(description='add more slurm jobs to an experiment.')
    parser.add_argument('logdir', type=str, help='log directory.')
    parser.add_argument('-n', '--njobs', type=int, help='The number of jobs to add.')
    parser.add_argument('-e', '--exps', nargs='*', type=str, help='Experiments to extend. leave blank to extend all jobs.')
    args = parser.parse_args()
    main(args.logdir, args.njobs, args.exps)
