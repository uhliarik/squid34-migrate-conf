#!/usr/bin/python -tt
# -*- coding: utf-8 -*-
#
# This script will help you to prepare downgrade for squid-3.5
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
import traceback

class DowngradePrep:
    SQUID_LINK_PATHS=["/usr/share/squid/errors/zh-cn", "/usr/share/squid/errors/zh-tw"]
    DEFAULT_SQUID_CONF="/etc/squid/squid.conf"
    DEFAULT_BACKUP_EXT=".bak"
    DEFAULT_TMP_EXT=".tmp"
    RE_INCLUDE_CHECK="\s*include\s+(.*)"

    def process(self, squid_conf):
        remove_links()
        revert_squid_conf(squid_conf)

    def swap_files(self, first_file, second_file):
        tmp_file = get_tmp_filename(first_file)
        try:
            os.rename(first_file, tmp_file)
            os.rename(second_file, first_file)
            os.rename(tmp_file, second_file)
        except Exception as e:
            print "Error: {0}".format(e)
            sys.exit(1)

    def check_includes(self, line=''):
        m = re.match(SELF.RE_INCLUDE_CHECK, line)
        include_list = ""
        ret_list = []
        if not (m is None):
            include_list = re.split('\s+', m.group(1))
            for include_file in include_list:
                if os.path.isfile(include_file)
                    ret_list.append(include_file)
                    print "Found include %s config" % (include_file)
#                    print "%sRestoring squid config file: %s" % (include_file)
        return ret_list

    def get_includes(self, squid_conf):
        return []

    def find_includes(self):
        pass

    def revert_squid_conf(self, squid_conf):
        if (not os.path.isfile(squid_conf)):
            sys.stderr.write("Error: config file %s doesn't exist\n" % (squid_conf))
            sys.exit(1)

        # get all includes from squid conf
        includes = get_includes(squid_conf)

        # find backed-up squid conf file
        backup_conf = find_backup_filename(squid_conf)

        # there is no squid conf backup
        if (not os.path.isfile(backup_conf)):
            sys.stderr.write("Error: can not find backup config file: %s \n" % (backup_conf))
            return

        # move backup to new squid_conf and vice versa
        swap_files(backup_conf, squid_conf)

        # success
        print("Backed up squid conf file %s was successfully restored" % (squid_conf))

    def get_tmp_filename(self, moved_file):
        file_idx = 1
        tmp_fn = moved_file + self.DEFAULT_TMP_EXT

        while (os.path.isfile(tmp_fn)):
            tmp_fn = moved_file + DEFAULT_TMP_EXT + str(file_idx)

        return tmp_fn

    def find_backup_filename(self, squid_conf):
        file_idx = 1
        tmp_fn = self.squid_conf + self.DEFAULT_BACKUP_EXT

        while (os.path.isfile(tmp_fn)):
            tmp_fn = self.squid_conf + self.DEFAULT_BACKUP_EXT + str(file_idx)
            file_idx = file_idx + 1

        if (file_idx > 2):
            return self.squid_conf + self.DEFAULT_BACKUP_EXT + str(file_idx-2)
        else:
            return self.squid_conf + self.DEFAULT_BACKUP_EXT

    def remove_links(self):
        try:
            for link in DowngradePrep.SQUID_LINK_PATHS:
                print "Removing symlink: " + link
                if os.path.exists(link):
                     if os.path.islink(link):
                         os.remove(link)
                else:
                     print "Symlink has been already removed"
        except Exception as e:
            print "Error: {0}".format(e)
            sys.exit(1)

if __name__ == '__main__':
    script_dir = os.getcwd()

    squid_conf = DowngradePrep.DEFAULT_SQUID_CONF
    if (len(sys.argv) > 1):
        squid_conf = sys.argv[1]

    os.chdir(os.path.dirname(squid_conf))
    try:
        downgrade = DowngradePrep(squid_conf)
        downgrade.process()
    except:
        traceback.print_exc(file=sys.stdoutput)
    finally:
        os.chdir(script_dir)
