#!/usr/bin/env python

import os
import sys
import shutil

from argparse import ArgumentParser


def process_destination_directory(outdir, with_delete):
    if os.path.isdir(outdir) and with_delete:
        shutil.rmtree(outdir)
    elif os.path.isdir(outdir) and not with_delete:
        print("The directory '{}' already exists".format(outdir))
        sys.exit(1)
    os.mkdir(outdir)
