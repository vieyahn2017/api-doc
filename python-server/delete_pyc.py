#!/usr/bin/env python
# -*-coding:utf-8 -*-
#
# Author: tony - birdaccp at gmail.com
# Create by:2015-09-30 14:04:12
# Last modified:2015-11-27 16:24:19
# Filename:delete_pyc.py
# Description:

import os


class listFiles(object):
    def __init__(self, destPath):
        self.files = []
        self._listAllFile(destPath)

    def getAllFiles(self):
        return self.files

    def _listAllFile(self, destPath):
        lists = os.listdir(destPath)
        for l in lists:
            p = os.path.join(destPath, l)
            if os.path.isdir(p):
                self._listAllFile(p)
            elif os.path.isfile(p):
                self.files.append(p)


ls = listFiles(os.getcwd())
for l in ls.getAllFiles():
    file, ext = os.path.splitext(l)
    if not ext in ['.sh']:
        os.system("chmod -x '%s'" % l)

    if ext in ['.pyc']:
        print l
        os.unlink(l)
