import os, argparse, yaml
from shutil import copyfile, copytree
from subprocess import call


def main(logdir, exp, newlogdir, newexp):
    if newlogdir is not None:
        os.makedirs(newlogdir)
        os.makedirs(os.path.join(newlogdir, '.run'))
        os.makedirs(os.path.join(newlogdir, '.slurm'))
        os.makedirs(os.path.join(newlogdir, '.configs'))
        with open(os.path.join(logdir, '.config'), 'r') as f:
            params = yaml.load(f)
        params['logdir'] = os.path.abspath(newlogdir)
        with open(os.path.join(newlogdir, '.config'), 'w') as f:
            yaml.dump(params, f, default_flow_style=False)
        copyfile(os.path.join(logdir, '.run_script'), os.path.join(newlogdir, '.run_script'))
        call(['chmod', '+x', os.path.join(newlogdir, '.run_script')])
    else:
        newlogdir = logdir

    script_file = os.path.join(newlogdir, '.run_script')
    param_file  = os.path.join(newlogdir, '.configs', newexp + '.yaml')
    launch_file = os.path.join(newlogdir, '.run', newexp + '.sh')

    with open(launch_file, 'w') as f:
        f.write("#!/bin/bash\n")
        f.write(f"{os.path.abspath(script_file)} {os.path.abspath(param_file)}\n")
    call(['chmod', '+x', launch_file])

    with open(os.path.join(logdir, '.configs', exp + '.yaml'), 'r') as f:
        params = yaml.load(f)

    params['expdir'] = os.path.abspath(os.path.join(newlogdir, newexp))
    with open(param_file, 'w') as f:
        yaml.dump(params, f, default_flow_style=False)

    # copy exp folder
    copytree(os.path.join(logdir, exp), os.path.join(newlogdir, newexp))



if __name__=='__main__':
    parser = argparse.ArgumentParser(description='copy an experiment directory.')
    parser.add_argument('logdir', type=str, help='log directory.')
    parser.add_argument('exp', type=str, help='expname (i.e. exp0, exp1, etc).')
    parser.add_argument('newexp', type=str, help='new expname')
    parser.add_argument('-l', '--newlogdir', type=str, default=None, help='If provided, copy to new log directory')
    args = parser.parse_args()
    main(args.logdir, args.exp, args.newlogdir, args.newexp)
