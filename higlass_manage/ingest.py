import click
import clodius.cli.aggregate as cca
import ntpath
import os.path as op
import sys

from higlass_manage.common import fill_filetype_and_datatype
from higlass_manage.common import import_file
from higlass_manage.common import get_temp_dir
from higlass_manage.start import _start

@click.command()
@click.argument('filename')
@click.option('--hg-name', default='default', 
        help='The name of the higlass container to import this file to')
@click.option('--filetype', default=None, help="The type of file to ingest (e.g. cooler)")
@click.option('--datatype', default=None, help="The data type of in the input file (e.g. matrix)")
@click.option('--assembly', default=None, help="The assembly that this data is mapped to")
@click.option('--name', default=None, help="The name to use for this file")
@click.option('--uid', default=None, help='The uuid to use for this file')
@click.option('--no-upload', default=None, is_flag=True, help="Do not copy the file to the media directory. File must already be in the media directory.")
@click.option('--chromsizes-filename', default=None, help="A set of chromosome sizes to use for bed and bedpe files")
@click.option('--has-header', default=False, is_flag=True, help="Does the input file have column header information (only relevant for bed or bedpe files)")
@click.option('--project-name', default=None, help='Group this tileset with others by specifying a project name')
def ingest(filename, 
        hg_name, 
        filetype=None, 
        datatype=None, 
        assembly=None, 
        name=None, 
        chromsizes_filename=None, 
        has_header=False, 
        uid=None, 
        no_upload=None,
        project_name=None):
    '''
    Ingest a dataset
    '''
    _ingest(filename,
            hg_name,
            filetype,
            datatype,
            assembly,
            name,
            chromsizes_filename,
            has_header,
            uid,
            no_upload,
            project_name
            )

def _ingest(filename, 
        hg_name, 
        filetype=None, 
        datatype=None, 
        assembly=None, 
        name=None, 
        chromsizes_filename=None, 
        has_header=False, 
        uid=None, 
        no_upload=None,
        project_name=None):

    try:
        get_temp_dir(hg_name)
    except Exception:
        print("HiGlass not running. Starting...")
        _start(hg_name=hg_name)

    if not no_upload and (not op.exists(filename) and not op.islink(filename)):
        print('File not found:', filename, file=sys.stderr)
        return None

    # guess filetype and datatype if they're None
    (filetype, datatype) = fill_filetype_and_datatype(filename, filetype, datatype)
    
    temp_dir = get_temp_dir(hg_name)
    (to_import, filetype) = aggregate_file(filename, filetype, assembly, chromsizes_filename, has_header, no_upload, temp_dir)

    return import_file(hg_name, to_import, filetype, datatype, assembly, name, uid, no_upload, project_name)

def aggregate_file(filename, filetype, assembly, chromsizes_filename, has_header, no_upload, tmp_dir):
    if filetype == 'bedfile':
        if no_upload:
            raise Exception("Bedfile files need to be aggregated and cannot be linked. Consider not using the --link-file option", file=sys.stderr)
            
        if assembly is None and chromsizes_filename is None:
            print('An assembly or set of chromosome sizes is required when importing bed files. Please specify one or the other using the --assembly or --chromsizes-filename parameters', file=sys.stderr)
            return

        output_file = op.join(tmp_dir, ntpath.basename(filename) + '.beddb')

        print("Aggregating bedfile")
        cca._bedfile(filename,
                output_file,
                assembly,
                importance_column='random',
                has_header=has_header,
                chromosome=None,
                max_per_tile=50,
                delimiter=None,
                chromsizes_filename=chromsizes_filename,
                offset=0,
                tile_size=1024)

        to_import = output_file

        # because we aggregated the file, the new filetype is beddb
        filetype='beddb'
        return (to_import, filetype)
    elif filetype == 'bedpe':
        if no_upload:
            raise Exception("Bedpe files need to be aggregated and cannot be linked. Consider not using the --link-file option", file=sys.stderr)
        if assembly is None and chromsizes_filename is None:
            print('An assembly or set of chromosome sizes is required when importing bed files. Please specify one or the other using the --assembly or --chromsizes-filename parameters', file=sys.stderr)
            return

        output_file = op.join(tmp_dir, filename + '.bed2ddb')

        print("Aggregating bedpe (output_file: {}".format(output_file))
        cca._bedpe(filename,
                output_file,
                assembly,
                importance_column='random',
                has_header=has_header,
                chromosome=None,
                max_per_tile=50,
                chromsizes_filename=chromsizes_filename,
                tile_size=1024)

        to_import = output_file

        # because we aggregated the file, the new filetype is beddb
        filetype='bed2ddb'
        return (to_import, filetype)
    else:
        return (filename, filetype)
