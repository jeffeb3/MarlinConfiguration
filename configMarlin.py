#!/usr/bin/env python

import sys
import os.path
from optparse import OptionParser
import subprocess
import logging
import shutil
import fileinput

# import yaml from pyyaml: http://pyyaml.org/wiki/PyYAMLDocumentation
from yaml import load as loadYaml
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

# Set the default logging to INFO
logging.basicConfig(format='%(levelname)s - %(message)s')
gLog = logging.getLogger()
gLog.setLevel(logging.INFO)

def getOptions():
    ''' Set the user interface for this application. '''
    parser = OptionParser()
    parser.description = \
    '''
This tool is used to generate configurations for Marlin, from a
specific version. It uses a specific diff format to configure
changes to the software, and tries to be as generic as possible,
but it's written specifically for the changes needed for the machines
made by vicious1.com.

License is MIT.
    '''
    parser.add_option('-c', '--config', dest='config',
                     help='Config file that describes the changes needed to configure Marlin')
    parser.add_option('-n', '--name', dest='name', default='Marlin_MPCNC',
                     help='Name that describes this firmware')
    parser.add_option('-v', '--verbose', dest='verbose', default=False, action='store_true',
                     help='Set to see more of the steps being taken. Useful for debugging')
    parser.add_option('-g', '--git-server', dest='git_server', default="https://github.com/MarlinFirmware/Marlin",
                     help='Location to get Marlin from, in standard git clone syntax.')
    parser.add_option('-t', '--git-tag', dest='git_tag', default="1.1.x",
                     help='Tag or branch name to use for the checkout')

    options, _ = parser.parse_args()

    if not options.config or not os.path.exists(options.config):
        gLog.fatal("Missing Config. Aborting.")
        sys.exit(-1)

    if options.verbose:
        # Allow more message through.
        gLog.setLevel(logging.DEBUG)

    gLog.debug('options:\n' + str(options))
    return options

def cloneRepo(git_server, git_tag):
    ''' Clone a repo, to a specific branch or tag. '''

    gLog.info('Cloning Marlin')
    gLog.debug("Marlin repo: '{}'".format(git_server))
    gLog.debug("Marlin tag:  '{}'".format(git_tag))
    # Clone the repo, with the appropriate tag
    proc = subprocess.Popen(['git', 'clone', '-b', git_tag, git_server, 'Marlin'],
                            stdout=None, stderr=None, shell=False)
    proc.wait()

    ok = proc.returncode == 0

    if not ok:
        gLog.fatal('Failed to clone Marlin. See above for details')

    return ok

if __name__ == '__main__':

    options = getOptions()

    # read in the config (difference) file
    with open(options.config, 'r') as configFile:
        config = loadYaml(configFile, Loader=Loader)
    gLog.debug("Config:\n" + str(config))

    if not cloneRepo(options.git_server, options.git_tag):
        sys.exit(-2)

    for filename in config:
        gLog.debug('editing {}'.format('Marlin' + os.sep + filename))
        file = fileinput.FileInput('Marlin' + os.sep + filename, inplace=True)
        for line in file:
            for (before, after) in config[filename]:
                if before in line:
                    line = line.replace(before, after)
            print line,

    # Copy the Marlin/Marlin folder to it's own place.
    shutil.copytree('Marlin' + os.sep + 'Marlin', options.name)

    shutil.move(options.name + os.sep + 'Marlin.ino', options.name + os.sep + options.name + '.ino')

    # remove the example configurations
    shutil.rmtree(options.name + os.sep + 'example_configurations')

    # Clean up the Marlin folder
    shutil.rmtree('Marlin')
