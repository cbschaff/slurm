import os, argparse, glob, yaml
from subprocess import call
from zlib import adler32 as hash_fn


def main(logdir, njobs, exps):
    logdir = os.path.abspath(logdir)

    if len(exps) == 0:
        launch_files = glob.glob(os.path.join(logdir, '.run/*'))
    else:
        launch_files = [os.path.join(logdir, '.run', f'{e}.sh') for e in exps]

    with open(os.path.join(logdir, '.config'), 'r') as f:
        c = yaml.load(f)

    id = abs(hash_fn(str.encode(logdir)))
    for lf in launch_files:
        e = os.path.basename(lf)[:-3]
        cmd = f'sbatch -d singleton -J {e}_{id}'
        for flag, value in c['slurm'].items():
            cmd += f' --{flag} {value}' if len(flag) > 1 else f' -{flag} {value}'
        for _ in range(njobs):
            outfile = os.path.join(logdir, f'.slurm/{e}_%j.out')
            call(cmd.split() + ['-o', outfile, lf])






if __name__=='__main__':
    parser = argparse.ArgumentParser(description='add more slurm jobs to an experiment.')
    parser.add_argument('logdir', type=str, help='log directory.')
    parser.add_argument('-n', '--njobs', type=int, default=1, help='The number of jobs to add.')
    parser.add_argument('-e', '--exps', nargs='*', default='', type=str, help='Experiments to extend. leave blank to extend all jobs.')
    args = parser.parse_args()
    main(args.logdir, args.njobs, args.exps)
