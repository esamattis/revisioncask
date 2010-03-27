# -*- coding: utf-8 -*-
"""
Copyright (C) 2010 Esa-Matti Suuronen <esa-matti@suuronen.org>

This file is part of subssh.

Subssh is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as 
published by the Free Software Foundation, either version 3 of 
the License, or (at your option) any later version.

Subssh is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public 
License along with Subssh.  If not, see 
<http://www.gnu.org/licenses/>.
"""



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
    
    
