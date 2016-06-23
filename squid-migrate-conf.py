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

    def __init__(self, args=None, level=0):
        if (len(args) > 0):
            self.squid_conf = args[0]
        else:
            self.squid_conf = ConfMigration.DEFAULT_SQUID_CONF

        self.level = level
        if (not os.path.isfile(self.squid_conf)):
            sys.stderr.write("%sError: config file %s doesn't exist\n" % (self.get_prefix_str(), self.squid_conf))
            sys.exit(1)

        self.squid_bak_conf = self.get_backup_name()

        self.migrated_squid_conf_data = []
        self.squid_conf_data = None

        print ("%sSquid conf is: " + self.squid_conf) % self.get_prefix_str()

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
             # TODO: add better splitting - it is naive now
             include_list = m.group(1).split(" ")
             for include_file in include_list:
                 print "%sFound include %s config" % (self.get_prefix_str(), include_file)
                 if os.path.isfile(include_file):
                     print "%sMigrating included %s config" % (self.get_prefix_str(), include_file)
                     conf = ConfMigration([include_file], self.level+1)
                     conf.migrate()

    def process_conf_lines(self):
        for line in self.squid_conf_data.split(os.linesep):
            self.check_include(line)
            line = re.sub(self.RE_LOG_ACCESS, self.RE_LOG_ACCESS_REP, line)
            line = re.sub(self.RE_LOG_ICAP, self.RE_LOG_ICAP_REP, line)
            self.migrated_squid_conf_data.append(line)

    def migrate(self):
        self.read_conf()
        self.process_conf_lines()
        self.write_conf()
        print "%sMigration successfully finished" % (self.get_prefix_str())

    def get_prefix_str(self):
        return (("    " * self.level) + "["+  self.squid_conf + "]: ")

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
        print ("%sCreating backup conf: " + self.squid_bak_conf) % (self.get_prefix_str())
        try:
           shutil.copyfile(self.squid_conf, self.squid_bak_conf)
           self.out_file = open(self.squid_conf, "w")
           self.out_file.write(os.linesep.join(self.migrated_squid_conf_data))
           self.out_file.close()
        except Exception as e:
           sys.stderr.write("%s Error: %s\n" % (self.get_prefix_str, e))
           sys.exit(1)

if __name__ == '__main__':
    conf = ConfMigration(sys.argv[1:], 0)
    conf.migrate()

