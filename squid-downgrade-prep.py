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

# TODO: add possibility to revert changes caused by migrate script

class DowngradePrep:
    SQUID_LINK_PATHS=["/usr/share/squid/errors/zh-cn", "/usr/share/squid/errors/zh-tw"]

    def process(self):
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
    downgrade = DowngradePrep()
    downgrade.process()

