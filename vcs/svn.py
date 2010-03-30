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

import os
from ConfigParser import SafeConfigParser

import subssh
from abstractrepo import VCS
from repomanager import RepoManager


class config:
    SVNSERVE_BIN = "svnserve"
    
    SVN_BIN = "svn"
    
    SVNADMIN_BIN = "svnadmin"
    
    REPOSITORIES = os.path.join( os.environ["HOME"], "repos", "svn" )

    WEB_DIR = os.path.join( os.environ["HOME"], "repos", "websvn" )
    
    
    URL_RW =  "svn+ssh://$hostusername@$hostname/$name_on_fs"
    URL_WEB_VIEW =  "http://$hostname/websvn/listing.php?repname=$name_on_fs"    
    
    
    URLS = """Read/Write|svn+ssh://$hostname/$name_on_fs
Webview|http://$hostname/websvn/$name_on_fs"""

    WEBDIR = os.path.join( os.environ["HOME"], "repos", "websvn" )

    MANAGER_TOOLS = "true"

class Subversion(VCS):
    required_by_valid_repo = ("conf/svnserve.conf",)
    permdb_name= "conf/" + VCS.permdb_name
    # For svnserve, "/" stands for whole repository
    _permissions_section = "/"
    


class SubversionManager(RepoManager):
    
    klass = Subversion
    
    def _enable_svn_perm(self, path, dbfile="authz"):
        """
        Set Subversion repository to use our permission config file
        """
        confpath = os.path.join(path, "conf/svnserve.conf")
        conf = SafeConfigParser()
        conf.read(confpath)
        conf.set("general", "authz-db", dbfile)
        f = open(confpath, "w")
        conf.write(f)
        f.close()


    def create_repository(self, path, owner):
        
        if not os.path.exists(path):
            os.makedirs(path)
        path = os.path.abspath(path)
        
        subssh.check_call((config.SVNADMIN_BIN, "create", path))
        subssh.check_call((
                          config.SVN_BIN, "-m", "created automatically project base", 
                          "mkdir", "file://%s" % os.path.join(path, "trunk"),
                                   "file://%s" % os.path.join(path, "tags"),
                                   "file://%s" % os.path.join(path, "branches"),
                          ))
    
        
        self._enable_svn_perm(path, os.path.basename(Subversion.permdb_name))
        
        return 0


    




@subssh.no_interactive
@subssh.expose_as("svnserve")
def handle_svn(user, *args):
    # Subversion can handle itself permissions and virtual root.
    # So there's no need to manually check permissions here or
    # transform the virtual root.
    return subssh.call((config.SVNSERVE_BIN, 
                            '--tunnel-user=' + user.username,
                            '-t', '-r',  
                            config.REPOSITORIES))
    
    
    
    



def __appinit__():
    if subssh.to_bool(config.MANAGER_TOOLS):
        manager = SubversionManager(config.REPOSITORIES, 
                                    web_repos_path=config.WEB_DIR,
                                    urls={'rw': config.URL_RW,
                                          'webview': config.URL_WEB_VIEW},                                    
                                     )
        
        subssh.expose_instance(manager, prefix="svn-")

