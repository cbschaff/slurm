import os, argparse, yaml
from subprocess import call
from shutil import copyfile
import numpy as np
from zlib import adler32 as hash_fn


class Jobs:
    def __init__(self, config):
        self.config = config

    def sample(self, param):
        p = self.config['params'][param]
        if not isinstance(p, dict):
            return p
        scale = p['scale'] if 'scale' in p else 'linear'

        if 'range' in p:
            minv, maxv = p['range']
            if scale == 'log':
                minv = np.log(minv)
                maxv = np.log(maxv)

            v = np.random.rand() * (maxv - minv) + minv

            if scale == 'log':
                v = np.exp(v)
            return float(v)

        elif 'values' in p:
            return p['values'][np.random.randint(len(p['values']))]


        else:
            assert False, "Possible parameter values must be defined with range or values keys."

    def get_value(self, param, index):
        p = self.config['params'][param]
        if not isinstance(p, dict):
            return p if index==0 else None

        assert 'values' in p, "All non-constant parameters must have the values attribute to use Grid Search."

        return p['values'][index] if index < len(p['values']) else None


    def __iter__(self):
        self.n = 0
        self.counts = np.zeros(len(self.config['params']), dtype=np.int32)
        return self

    def __next__(self):
        if self.config['algorithm'] == 'random':
            return self._next_random()
        if self.config['algorithm'] == 'grid':
            return self._next_grid()

        assert False, "Unkown algorithm"


    def _next_random(self):
        if self.n >= self.config['nexps']:
            raise StopIteration

        self.n += 1
        params = {}
        for param in self.config['params']:
            params[param] = self.sample(param)
        return params

    def _next_grid(self):
        param_names = sorted(self.config['params'].keys())
        params = {}

        for i,p in reversed(list(enumerate(param_names))):
            v = self.get_value(p, self.counts[i])
            if v is None:
                if i == 0:
                    raise StopIteration
                else:
                    self.counts[i] = 0
                    self.counts[i-1] += 1
                    v = self.get_value(p, self.counts[i])

            params[p] = v

        self.counts[-1] += 1
        return params



def main(config_file, run_script):
    with open(config_file, 'r') as f:
        c = yaml.load(f)

    logdir = os.path.abspath(c['logdir'])
    prefix = c['prefix'] if 'prefix' in c else 'exp'

    script_file = os.path.join(logdir, '.run_script')

    os.makedirs(logdir, exist_ok=True)
    os.makedirs(os.path.join(logdir, '.run'), exist_ok=True)
    os.makedirs(os.path.join(logdir, '.slurm'), exist_ok=True)
    os.makedirs(os.path.join(logdir, '.configs'), exist_ok=True)
    copyfile(config_file, os.path.join(logdir, '.config'))
    copyfile(run_script, script_file)
    call(['chmod', '+x', script_file])

    for i,ps in enumerate(Jobs(c)):

        expdir =  os.path.join(logdir, f'{prefix}{i}')
        param_file = os.path.join(logdir, f'.configs/{prefix}{i}.yaml')

        with open(param_file, 'w') as f:
            yaml.dump({'expdir': expdir, 'params': ps}, f, default_flow_style=False)

        exp_launch = os.path.join(logdir, f'.run/{prefix}{i}.sh')
        with open(exp_launch, 'w') as f:
            f.write("#!/bin/bash\n")
            f.write(f"{script_file} {param_file}\n")
        call(['chmod', '+x', exp_launch])

        id = abs(hash_fn(str.encode(logdir)))
        cmd = f'sbatch -d singleton -J {prefix}{i}_{id}'
        for flag, value in c['slurm'].items():
            cmd += f' --{flag} {value}' if len(flag) > 1 else f' -{flag} {value}'
        for _ in range(c['njobs']):
            outfile = os.path.join(logdir, f'.slurm/{prefix}{i}_%j.out')
            call(cmd.split() + ['-o', outfile, exp_launch])






if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Launch slurm jobs.')
    parser.add_argument('config', type=str, help='Config file.')
    parser.add_argument('script', type=str, help='script which runs experiments. Its required interface is described in README.md')
    args = parser.parse_args()
    main(args.config, args.script)
