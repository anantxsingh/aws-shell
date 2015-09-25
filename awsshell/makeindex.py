"""Module for building the autocompletion indices."""
import os
import sys
import argparse
import pprint

try:
    import awscli.clidriver
    from awscli.argprocess import ParamShorthandDocGen
except ImportError:
    print "Couldn't import awscli: pip install awscli"
    sys.exit(0)

from awsshell import determine_index_filename
from awsshell.utils import remove_html


SHORTHAND_DOC = ParamShorthandDocGen()


def new_index():
    return {'arguments': [], 'argument_metadata': {},
            'commands': [], 'children': {}}



def index_command(index_dict, help_command):
    arg_table = help_command.arg_table
    for arg in arg_table:
        arg_obj = arg_table[arg]
        metadata = {
            'required': arg_obj.required,
            'type_name': arg_obj.cli_type_name,
            'minidoc': '',
            'example': '',
        }
        if arg_obj.documentation:
            metadata['minidoc'] = remove_html(arg_obj.documentation.split('\n')[0])
        if SHORTHAND_DOC.supports_shorthand(arg_obj.argument_model):
            example = SHORTHAND_DOC.generate_shorthand_example(
                arg, arg_obj.argument_model)
            metadata['example'] = example

        index_dict['arguments'].append('--%s' % arg)
        index_dict['argument_metadata']['--%s' % arg] = metadata
    for cmd in help_command.command_table:
        index_dict['commands'].append(cmd)
        # Each sub command will trigger a recurse.
        child = new_index()
        index_dict['children'][cmd] = child
        sub_command = help_command.command_table[cmd]
        sub_help_command = sub_command.create_help_command()
        index_command(child, sub_help_command)


def write_index(output_filename=None):
    if output_filename is None:
        output_filename = determine_index_filename()
    driver = awscli.clidriver.create_clidriver()
    help_command = driver.create_help_command()
    index = {'aws': new_index()}
    current = index['aws']
    index_command(current, help_command)

    result = pprint.pformat(index)
    if not os.path.isdir(os.path.dirname(output_filename)):
        os.makedirs(os.path.dirname(output_filename))
    with open(output_filename, 'w') as f:
        f.write(result)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--output',
                        help='The filename of the index file.')
    args = parser.parse_args()
    if args.output is None:
        args.output = determine_index_filename()
    write_index(args.output)