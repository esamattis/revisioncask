# -*- coding: utf-8 -*-
'''
Created on Mar 9, 2010

@author: epeli
'''

import subssh

@subssh.expose_as()
def whoami(user):
    """Tells who you are
    """
    subssh.writeln(user.username)


