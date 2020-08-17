#!/bin/env python

import yaml, sys
from subprocess import call

with open(sys.argv[1], 'r') as f:
    config = yaml.load(f)

print(config)
