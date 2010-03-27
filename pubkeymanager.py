# -*- coding: utf-8 -*-
'''
Created on Mar 21, 2010

@author: epeli
'''



import subssh
from subssh import admintools



@subssh.expose_as("addkey")
def add_key(user, *args):
    """
    Add new public key.
    
    usage:
    
    from web:
        $cmd http://example.com/mykey.pub
    
    from args:
        $cmd ssh-rsa AAAthekeyitself... 
        
    from stdin:
        you@home:~$$ cat mykey.pub | ssh $hostusername@$hostname $cmd -
    
    """
    if not args:
        raise subssh.InvalidArguments("At least one argument is required")
    
    return admintools.add_key(user.username, args)


@subssh.expose_as("listkeys")    
def list_keys(user):    
    """List keys you've uploaded"""
    return admintools.list_keys(user.username)
    
    
