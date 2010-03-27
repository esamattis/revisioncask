# -*- coding: utf-8 -*-

'''
Created on Mar 5, 2010

@author: epeli
'''


import subssh

class config:
    HELLO = "default hello"




@subssh.expose_as("uptime")
def uptime(user):
    """Example application for integrating uptime of the host system"""
    subssh.writeln(config.HELLO)
    return subssh.call(("uptime"))

    


