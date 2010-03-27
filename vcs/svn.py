# -*- coding: utf-8 -*-

'''
Created on Mar 5, 2010

@author: epeli
'''

"""
svnadmin create testi
svn -m "created project base" mkdir file:///$(pwd)/testi/trunk file:///$(pwd)/testi/tags



epeli@debian:~/repos/svn/testi$ tail conf/authz  -n 4
[/]
essuuron = rw
* = r


epeli@debian:~/repos/svn/testi$ cat conf/svnserve.conf
...
[general]
authz-db = authz
...

"""


import os
from ConfigParser import SafeConfigParser

import subssh
from abstractrepo import VCS
from repomanager import RepoManager
from repomanager import parse_url_configs


class config:
    SVNSERVE_BIN = "svnserve"
    
    SVN_BIN = "svn"
    
    SVNADMIN_BIN = "svnadmin"
    
    REPOSITORIES = os.path.join( os.environ["HOME"], "repos", "svn" )

    WEBVIEW = os.path.join( os.environ["HOME"], "repos", "websvn" )
    
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
                                    urls=parse_url_configs(config.URLS),
                                    webdir=config.WEBDIR )
        
        subssh.expose_instance(manager, prefix="svn-")

