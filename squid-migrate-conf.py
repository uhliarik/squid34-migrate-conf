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
    RE_LOG_ACCESS="log_access\s+(\w+)\s+"
    RE_LOG_ACCESS_DENY_REP="access_log none "
    RE_LOG_ACCESS_ALLOW_REP="access_log daemon:/var/log/squid/access.log squid "
    RE_LOG_ACCESS_TEXT="log_access"

    RE_LOG_ICAP="log_icap\s+"
    RE_LOG_ICAP_REP="icap_log daemon:/var/log/squid/icap.log "
    RE_LOG_ICAP_TEXT="log_icap"

    RE_HIER_STOPLIST="hierarchy_stoplist\s+(.*)"
    RE_HIER_STOPLIST_REP="acl %s url_regex %s\nalways_direct allow %s"
    RE_HIER_STOPLIST_TEXT="hierarchy_stoplist"

    HIER_ACL_NAME="migrated_hs_%d_%d"

    RE_INCLUDE_CHECK="\s*include\s+(.*)"

    COMMENT_FMT="# migrated automatically by squid-migrate-conf, the original configuration was: %s\n%s"

    DEFAULT_SQUID_CONF="/etc/squid/squid.conf"
    DEFAULT_BACKUP_EXT=".bak"
    DEFAULT_LEVEL_INDENT=3

    MAX_NESTED_INCLUDES=16

    def __init__(self, args, level=0, squid_conf='', conf_seq=0):
        self.args = args

        if squid_conf:
            self.squid_conf = squid_conf
        else:
            self.squid_conf = args.squid_conf
        self.write_changes = args.write_changes
        self.debug = args.debug

        self.conf_seq = conf_seq
        self.acl_seq = 0

        self.line_num = 0
        self.level = level
        if (not os.path.isfile(self.squid_conf)):
            sys.stderr.write("%sError: the config file %s does not exist\n" % (self.get_prefix_str(), self.squid_conf))
            sys.exit(1)

        self.squid_bak_conf = self.get_backup_name()

        self.migrated_squid_conf_data = []
        self.squid_conf_data = None


        print ("Migrating: " + self.squid_conf)

    def print_info(self, text=''):
        if (self.debug):
            print "%s%s" % (self.get_prefix_str(), text)

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
                 # included file can be written in regexp syntax
                 for include_file in glob.glob(include_file_re):
                     self.print_info("A config file %s was found and it will be included" % (include_file))
                     if os.path.isfile(include_file):
                         self.print_info("Migrating the included config file %s" % (include_file))
                         conf = ConfMigration(self.args, self.level+1, include_file, self.conf_seq+1)
                         conf.migrate()

                 # check, if included file exists
                 if (len(glob.glob(include_file_re)) == 0 and not (os.path.isfile(include_file_re))):
                     self.print_info("The config file %s does not exist." % (include_file_re))

    def print_sub_text(self, text, new_str):
        if self.write_changes:
            print "File: '%s', line: %d - the directive %s was replaced by %s" % (self.squid_conf, self.line_num, text, new_str)
        else:
            print "File: '%s', line: %d - the directive %s could be replaced by %s" % (self.squid_conf, self.line_num, text, new_str)

    def add_conf_comment(self, old_line, line):
        return self.COMMENT_FMT % (old_line, line)

    def sub_line_ad(self, line, line_re, allow_sub, deny_sub, text):
        new_line = line
        m = re.match(line_re, line)
        if not (m is None):
            # check, if allow or deny was used and select coresponding sub
            sub_text = allow_sub
            if (re.match('allow', m.group(1), re.IGNORECASE)):
                new_line = re.sub(line_re, sub_text, line)
            elif (re.match('deny', m.group(1), re.IGNORECASE)):
                sub_text = deny_sub
                new_line = re.sub(line_re, sub_text, line)

            # print out, if there was any change and add comment to conf line, if so
            if not (new_line is line):
                self.print_sub_text(text + " " +  m.group(1), sub_text)
                new_line = self.add_conf_comment(line, new_line)

        return new_line

    def sub_line(self, line, line_re, sub, text):
        new_line = line
        m = re.match(line_re, line)
        if not (m is None):
            new_line = re.sub(line_re, sub, line)

            # print out, if there was any change and add comment to conf line, if so
            if not (new_line is line):
                self.print_sub_text(text, sub)
                new_line = self.add_conf_comment(line, new_line)

        return new_line

    def rep_hier_stoplist(self, line, sub, words):
        wordlist = words.split(' ')

        esc_wordlist = []
        for w in wordlist:
            esc_wordlist.append(re.escape(w))

        # unique acl name for hierarchy_stoplist acl
        acl_name = self.HIER_ACL_NAME % (self.conf_seq, self.acl_seq)
        return sub % (acl_name, ' '.join(esc_wordlist), acl_name)

    def sub_hier_stoplist(self, line, line_re, sub, text):
        new_line = line
        m = re.match(line_re, line)
        if (not (m is None)):
            new_line = self.rep_hier_stoplist(line, sub, m.group(1))

        # print out, if there was any change and add comment to conf line, if so
        if not (new_line is line):
            self.print_sub_text(text, sub)
            new_line = self.add_conf_comment(line, new_line)

        return new_line

    def process_conf_lines(self):
        for line in self.squid_conf_data.split(os.linesep):

            # do not migrate comments
            if not line.strip().startswith('#'):
               self.check_include(line)
               line = self.sub_line_ad(line, self.RE_LOG_ACCESS, self.RE_LOG_ACCESS_ALLOW_REP, self.RE_LOG_ACCESS_DENY_REP, self.RE_LOG_ACCESS_TEXT)
               line = self.sub_line(line, self.RE_LOG_ICAP, self.RE_LOG_ICAP_REP, self.RE_LOG_ICAP_TEXT)
               line = self.sub_hier_stoplist(line, self.RE_HIER_STOPLIST, self.RE_HIER_STOPLIST_REP, self.RE_HIER_STOPLIST_TEXT)

            self.migrated_squid_conf_data.append(line)

            self.line_num = self.line_num + 1

    def migrate(self):
        # prevent infinite loop
        if (self.level > ConfMigration.MAX_NESTED_INCLUDES):
            sys.stderr.write("WARNING: the maximum number of nested includes was reached\n")
            return

        self.read_conf()
        self.process_conf_lines()
        if self.write_changes:
            if (not (set(self.migrated_squid_conf_data) == set(self.squid_conf_data.split(os.linesep)))):
                self.write_conf()

        self.print_info("The migration finished successfully")

    def get_prefix_str(self):
        return (("    " * int(self.level)) + "["+  self.squid_conf + "@%d]: " % (self.line_num))

    def read_conf(self):
        self.print_info("Reading squid conf: " + self.squid_conf)
        try:
           self.in_file = open(self.squid_conf, 'r')
           self.squid_conf_data = self.in_file.read()
           self.in_file.close()
        except Exception as e:
           sys.stderr.write("%sError: %s\n" % (self.get_prefix_str(), e))
           sys.exit(1)

    def write_conf(self):
        self.print_info("Creating backup conf: %s" % (self.squid_bak_conf))
        self.print_info("Writing changes to: %s" % (self.squid_conf))
        try:
           shutil.copyfile(self.squid_conf, self.squid_bak_conf)
           self.out_file = open(self.squid_conf, "w")
           self.out_file.write(os.linesep.join(self.migrated_squid_conf_data))
           self.out_file.close()
        except Exception as e:
           sys.stderr.write("%s Error: %s\n" % (self.get_prefix_str(), e))
           sys.exit(1)

def parse_args():
    parser = argparse.ArgumentParser(description='The script migrates the squid 3.3 configuration files to configuration files which are compatible with squid 3.5.')
    parser.add_argument('--conf', dest='squid_conf', action='store',
                        default=ConfMigration.DEFAULT_SQUID_CONF,
                        help='specify filename of squid configuration (default: %s)' % (ConfMigration.DEFAULT_SQUID_CONF))
    parser.add_argument('--write-changes', dest='write_changes', action='store_true',
                        default=False,
                        help='The changes are written to corresponding configuration files')
    parser.add_argument('--debug', dest="debug", action='store_true', default=False, help='print debug messages to stderr')
    return parser.parse_args()

if __name__ == '__main__':
    # parse args from command line
    args = parse_args()

    # check if config file exists
    if (not os.path.exists(args.squid_conf)):
        sys.stderr.write("Error: the file %s does not exist\n" % (args.squid_conf))
        sys.exit(1)

    # change working directory
    script_dir = os.getcwd()
    if (os.path.dirname(args.squid_conf)):
        os.chdir(os.path.dirname(args.squid_conf))

    # start migration
    try:
        conf = ConfMigration(args, 0)
        conf.migrate()
    finally:
        print ""

        if not args.write_changes:
            print "The changes have NOT been written to config files.\nUse the --write-changes option to write the changes"
        else:
            print "The changes have been written to config files!"

        os.chdir(script_dir)
