#!/usr/bin/env python

import os
import sys
import shutil

from argparse import ArgumentParser

from file_io_multiphase_tecplot import HeaderData
from file_io_multiphase_tecplot import read_tecplot
from file_io_multiphase_tecplot import write_tecplot


# Print iterations progress
def print_progress_bar(iteration, total, prefix='', suffix='', decimals=1, length=100, fill='█', print_end="\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end=print_end)
    # Print New Line on Complete
    if iteration == total:
        print()


def get_cmd_line_parser():
    parser = ArgumentParser()

    parser.add_argument("tecplot_file", help="the multi-zone tecplot file to separate")
    parser.add_argument("dir", help="the destination directory to put separated tecplot files")
    parser.add_argument("--delete", help="delete the destination directory if it exists", action="store_true")

    return parser


def process_destination_directory(args):
    if os.path.isdir(args.dir) and args.delete:
        shutil.rmtree(args.dir)
    elif os.path.isdir(args.dir) and not args.delete:
        print("The directory '{}' already exists".format(args.dir))
        sys.exit(1)
    os.mkdir(args.dir)


def main():
    parser = get_cmd_line_parser()
    args = parser.parse_args()

    process_destination_directory(args)

    data = read_tecplot(args.tecplot_file)

    for field_id in range(data['nfields']):
        #output_file = os.path.join(args.dir, "neb_{:04d}.tec".format(field_id))
        output_file = os.path.join(args.dir, args.tecplot_file[0:-4] + "_{:04d}.tec".format(field_id) )
        header_data = HeaderData()
        header_data.title = "neb_{:04d}.tec".format(field_id)
        header_data.variables = ['X', 'Y', 'Z', 'Mx', 'My', 'Mz', 'SD']
        write_tecplot(output_file, header_data, data, field_idx=field_id)
        print_progress_bar(field_id+1, data['nfields'], prefix="Progress:", suffix="Complete", length=100)


if __name__ == "__main__":
    main()
