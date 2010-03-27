'''
Created on Mar 23, 2010

@author: epeli


Simple application examples

'''

import subssh


@subssh.expose_as("hello")
def hello(user, name):
    """
    Says hello to you
    
    usage: $cmd <your name>
    """
    print "Hello %s!" % name



@subssh.expose_as("uptime")
def uptime(user):
    """
    Displays uptime of the system
    
    Example application for integrating uptime of the host system
    
    """
    return subssh.call(("uptime"))

    





        
        