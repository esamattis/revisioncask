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



Simple application examples
"""

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

    





        
        