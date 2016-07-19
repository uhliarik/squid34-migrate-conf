#!/usr/bin/python -tt
# -*- coding: utf-8 -*-
#
# This script will help you with migration squid-3.3 conf files to squid-3.5 conf files
# Copyright (C) 2016 Red Hat, Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# he Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Authors: Lubos Uhliarik <luhliari@redhat.com>

import sys
import os
import re
import shutil
import traceback
import argparse
import glob

class ConfMigration:
    # TODO: maybe change to dict + add more changes
    RE_LOG_ACCESS="log_access\s+"
    RE_LOG_ACCESS_REP="access_log none "
    RE_LOG_ICAP="log_icap\s+"
    RE_LOG_ICAP_REP="icap_log none "
    RE_INCLUDE_CHECK="\s*include\s+(.*)"

    DEFAULT_SQUID_CONF="/etc/squid/squid.conf"
    DEFAULT_BACKUP_EXT=".bak"
    DEFAULT_LEVEL_INDENT=3

    def __init__(self, args, level=0, squid_conf=''):
        self.args = args

        if squid_conf:
            self.squid_conf = squid_conf
        else:
            self.squid_conf = args.squid_conf
        self.write_changes = args.write_changes

        self.level = level
        if (not os.path.isfile(self.squid_conf)):
            sys.stderr.write("%sError: config file %s doesn't exist\n" % (self.get_prefix_str(), self.squid_conf))
            sys.exit(1)

        self.squid_bak_conf = self.get_backup_name()

        self.migrated_squid_conf_data = []
        self.squid_conf_data = None
        self.line_num = 0

        print ("%sSquid conf is: " + self.squid_conf) % self.get_prefix_str()

    def print_info(self, text=''):
        print ("%s%s", self.get_prefix_str(), text)

    def get_backup_name(self):
        file_idx = 1
        tmp_fn = self.squid_conf + self.DEFAULT_BACKUP_EXT

        while (os.path.isfile(tmp_fn)):
            tmp_fn = self.squid_conf + self.DEFAULT_BACKUP_EXT + str(file_idx)
            file_idx = file_idx + 1

        return tmp_fn

    #
    #  From squid config documentation:
    #
    #  Configuration options can be included using the "include" directive.
    #  Include takes a list of files to include. Quoting and wildcards are
    #  supported.
    #
    #  For example,
    #
    #  include /path/to/included/file/squid.acl.config
    #
    #  Includes can be nested up to a hard-coded depth of 16 levels.
    #  This arbitrary restriction is to prevent recursive include references
    #  from causing Squid entering an infinite loop whilst trying to load
    #  configuration files.
    #
    def check_include(self, line=''):
        m = re.match(self.RE_INCLUDE_CHECK, line)
        include_list = ""
        if not (m is None):
             include_list = re.split('\s+', m.group(1))
             for include_file_re in include_list:
                 for include_file in glob.glob(include_file_re):
                     print "%sFound include %s config" % (self.get_prefix_str(), include_file)
                     if os.path.isfile(include_file):
                         print "%sMigrating included %s config" % (self.get_prefix_str(), include_file)
                         conf = ConfMigration(self.args, self.level+1, include_file)
                         conf.migrate()

                 if (len(glob.glob(include_file_re)) == 0 and not (os.path.isfile(include_file_re))):
                     print "%sConfig %s doesn't exist!" % (self.get_prefix_str(), include_file_re)

    def sub_line(self, line, old_str, new_str):
        new_line = re.sub(old_str, new_str, line)
        if not (new_line is line):
            print "%s%s was replaced by %s" % (self.get_prefix_str(), old_str, new_str)
        return new_line

    def process_conf_lines(self):
        for line in self.squid_conf_data.split(os.linesep):
            self.check_include(line)
            line = self.sub_line(line, self.RE_LOG_ACCESS, self.RE_LOG_ACCESS_REP)
            line = self.sub_line(line, self.RE_LOG_ICAP, self.RE_LOG_ICAP_REP)
            self.migrated_squid_conf_data.append(line)

            self.line_num = self.line_num + 1

    def migrate(self):
        self.read_conf()
        self.process_conf_lines()
        if self.write_changes:
            if (not (set(self.migrated_squid_conf_data) == set(self.squid_conf_data.split(os.linesep)))):
                self.write_conf()

        print "%sMigration successfully finished" % (self.get_prefix_str())

    def get_prefix_str(self):
        return (("    " * self.level) + "["+  self.squid_conf + "@%d]: " % (self.line_num))

    def read_conf(self):
        print ("%sReading squid conf: " + self.squid_conf) % (self.get_prefix_str())
        try:
           self.in_file = open(self.squid_conf, 'r')
           self.squid_conf_data = self.in_file.read()
           self.in_file.close()
        except Exception as e:
           sys.stderr.write("%sError: %s\n" % (self.get_prefix_str(), e))
           sys.exit(1)

    def write_conf(self):
        print ("%sCreating backup conf: %s" ) % (self.get_prefix_str(), self.squid_bak_conf)
        print ("%sWriting changes to: %s" % (self.get_prefix_str(), self.squid_conf))
        try:
           shutil.copyfile(self.squid_conf, self.squid_bak_conf)
           self.out_file = open(self.squid_conf, "w")
           self.out_file.write(os.linesep.join(self.migrated_squid_conf_data))
           self.out_file.close()
        except Exception as e:
           sys.stderr.write("%s Error: %s\n" % (self.get_prefix_str, e))
           sys.exit(1)

def parse_args():
    parser = argparse.ArgumentParser(description='Migrate squid configuration files to configuration files, which are compatible with squid 3.5.')
    parser.add_argument('--conf', dest='squid_conf', action='store',
                        default=ConfMigration.DEFAULT_SQUID_CONF,
                        help='specify filename of squid configuration (default: %s)' % (ConfMigration.DEFAULT_SQUID_CONF))
    parser.add_argument('--write-changes', dest='write_changes', action='store_true',
                        default=False,
                        help='Changes are written to corresponding configuration files')
    return parser.parse_args()

if __name__ == '__main__':
    # parse args from command line
    args = parse_args()

    # check if config file exists
    if (not os.path.exists(args.squid_conf)):
        sys.stderr.write("Error: File doesn't exist: %s\n" % (args.squid_conf))
        sys.exit(1)

    # change working directory
    script_dir = os.getcwd()
    if (os.path.dirname(args.squid_conf)):
        os.chdir(os.path.dirname(args.squid_conf))

    # start migration
    try:
        conf = ConfMigration(args, 0)
        conf.migrate()
    except:
        traceback.print_exc(file=sys.stdout)
    finally:
        print "*"*80
        if not args.write_changes:
            print "CHANGES HAS NOT BEEN WRITTEN TO CONFIG FILES!\nUSE --write-changes OPTION TO WRITE CHANGES"
        else:
            print "CHANGES HAS BEEN WRITTEN TO CONFIG FILES!"
        print "*"*80
        os.chdir(script_dir)
