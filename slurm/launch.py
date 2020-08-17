import os, argparse, yaml
from subprocess import call
from shutil import copyfile
import numpy as np
from zlib import adler32 as hash_fn
from slurm import nest


class Parameter:
    def __init__(self, data):
        if isinstance(data, dict):
            self.scale = data['scale'] if 'scale' in data else 'linear'

            self.range = None
            if 'range' in data:
                minv, maxv = data['range']
                self.range = float(minv), float(maxv)
                if self.scale == 'log':
                    self.range = (np.log(v) for v in self.range)

            self.values = data['values'] if 'values' in data else None

            self.group = data['group'] if 'group' in data else None

        else:
            self.scale = 'linear'
            self.range = None
            self.values = [data]

    def sample(self):
        if self.range is not None:
            v = np.random.rand() * (self.range[1] - self.range[0]) + self.range[0]

            if self.scale == 'log':
                v = np.exp(v)
            return float(v)

        elif self.values is not None:
            return self.values[np.random.randint(len(self.values))]

        else:
            raise ValueError('Either range or values must be defined for random search.')


def is_parameter(data):
    if not isinstance(data, dict):
        return True

    for k in data:
        if k not in ['scale', 'range', 'values', 'group']:
            return False
    return True


nest.add_item_check(is_parameter)


class Jobs:
    def __init__(self, config):
        self.config = config
        self.structure = nest.get_structure(config['params'])
        self.params = [Parameter(p) for p in nest.flatten(config['params'])]

        self.independent_params = 0
        self.group_names = []
        for p in self.params:
            if p.group is None or p.group not in self.groups:
                self.independent_params += 1
                if p.group is not None:
                    self.group_names.append(p.group)

    def __iter__(self):
        if self.config['algorithm'] == 'random':
            return self._random_search_iter()
        if self.config['algorithm'] == 'grid':
            return self._grid_search_iter()

        assert False, "Unkown algorithm"

    def _random_search_iter(self):
        for _ in range(self.config['nexps']):
            yield nest.pack_sequence_as([p.sample() for p in self.params],
                                        self.structure)

    def _grid_search_iter(self):
        for flat_params in self._grid_search_recur(self.params):
            yield nest.pack_sequence_as(flat_params, self.structure)

    def _grid_search_recur(self, params, group_inds={}):
        p = params[0]
        if p.values is None:
            raise ValueError('The values attribute must be defined for all '
                             'parameters to use grid search!')

        if p.group is None:
            for v in p.values:
                for vals in self._grid_search_recur(params[1:], group_inds):
                    yield [v] + vals

        elif p.group in group_inds:
            ind = group_inds[p.group]
            if ind >= len(p.values):
                raise ValueError('All parameters in the same group must have '
                                 'the same number of values!')
            for vals in self._grid_search_recur(params[1:], group_inds):
                yield [p.values[ind]] + vals

        else:
            group_inds[p.group] = 0
            for v in p.values:
                for vals in self._grid_search_recur(params[1:], group_inds):
                    yield [v] + vals
                group_inds[p.group] += 1


def main(config_file, run_script):
    with open(config_file, 'r') as f:
        c = yaml.load(f)
    if 'slurm' not in c:
        raise ValueError("Your config file doesn't specify slurm parameters.")

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

    if 'p' in c['slurm'] and 'long' in c['slurm']['p']:
        timeout = '3.95d'
    else:
        timeout = '3.8h'
    for i, ps in enumerate(Jobs(c)):

        expdir = os.path.join(logdir, f'{prefix}{i}')
        param_file = os.path.join(logdir, f'.configs/{prefix}{i}.yaml')

        ps['logdir'] = expdir

        with open(param_file, 'w') as f:
            yaml.dump(ps, f, default_flow_style=False)

        exp_launch = os.path.join(logdir, f'.run/{prefix}{i}.sh')
        with open(exp_launch, 'w') as f:
            f.write("#!/bin/bash\n")
            f.write(f"timeout -s SIGINT {timeout} {script_file} {param_file}\n")

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
