import os
import typer
from rich.progress import track

from tecplot_utilities.separate_muti_zone_tecplot import process_destination_directory

from tecplot_utilities.file_io_multiphase_tecplot import read_tecplot
from tecplot_utilities.file_io_multiphase_tecplot import write_tecplot
from tecplot_utilities.file_io_multiphase_tecplot import HeaderData

app = typer.Typer()


@app.command()
def main(tecplot: str, outdir: str, with_delete: bool = False):
    r"""
    :param tecplot: the input tecplot file.
    :param outdir: the name of the output directory (by default this will *NOT* be removed if it exists).
    :param with_delete: delete the 'outdir' if it exists.
    """
    process_destination_directory(outdir, with_delete)

    data = read_tecplot(tecplot)

    for field_id in track(range(data['nfields']), description="Generating..."):
        #output_file = os.path.join(args.dir, "neb_{:04d}.tec".format(field_id))
        tecplot_leaf = os.path.split(tecplot)[-1]
        output_file = os.path.join(outdir, tecplot_leaf[0:-4] + "_{:04d}.tec".format(field_id) )
        header_data = HeaderData()
        header_data.title = "neb_{:04d}.tec".format(field_id)
        header_data.variables = ['X', 'Y', 'Z', 'Mx', 'My', 'Mz', 'SD']
        write_tecplot(output_file, header_data, data, field_idx=field_id)


def entry_point():
    app()


if __name__ == "__main__":
    app()
