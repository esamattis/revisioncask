# -*- coding: utf-8 -*-

'''
Created on Mar 5, 2010

@author: epeli



git config --global user.name "Oma Nimi" && git config --global user.email oma.nimi@oma.domain
'''

import os
import re


import subssh

from abstractrepo import VCS
from abstractrepo import InvalidPermissions
from repomanager import RepoManager
from repomanager import parse_url_configs


class config:
    GIT_BIN = "git"
    
    REPOSITORIES = os.path.join( os.environ["HOME"], "repos", "git" )
    
    WEBVIEW = os.path.join( os.environ["HOME"], "repos", "webgit" )

    MANAGER_TOOLS = "true"
    
    URLS = """Read/Write|ssh://$hostname/$name_on_fs
Read only clone|http://$hostname/repo/$name_on_fs
Webview|http://$hostname/gitphp/$name_on_fs"""

    WEBDIR = os.path.join( os.environ["HOME"], "repos", "webgit" )


class Git(VCS):
    
    required_by_valid_repo  = ("config", 
                               "objects",
                               "hooks")

    permissions_required = { "git-upload-pack":    "r",
                             "git-upload-archive": "r",
                             "git-receive-pack":   "rw" }    
    
    
    @property
    def name(self):
        name = os.path.basename(self.repo_path)    
        if self.repo_path.endswith(".git"):
            return name[:-4]
        return name
    
    def execute(self, username, cmd, git_bin="git"):
        
        if not self.has_permissions(username, self.permissions_required[cmd]):
            raise InvalidPermissions("%s has no permissions to run %s on %s" %
                                     (username, cmd, self.repo_name))                                 
        
        shell_cmd = cmd + " '%s'" %  self.repo_path

        return subssh.call((git_bin, "shell", "-c", shell_cmd))


class GitManager(RepoManager):
    klass = Git
    suffix = ".git"

    def create_repository(self, path, owner):
        
        os.chdir(path)
        
        subssh.check_call((config.GIT_BIN, "init", "--bare"))
        
        f = open("hooks/post-update", "w")
        f.write("""#!/bin/sh
#
# Prepare a packed repository for use over
# dumb transports.
#

exec git-update-server-info

""")
        f.close()
        
        os.chmod("hooks/post-update", 0700)
    
            




            

    
valid_repo = re.compile(r"^/[%s]+\.git$" % subssh.safe_chars)

@subssh.no_interactive
@subssh.expose_as("git-upload-pack", "git-receive-pack", "git-upload-archive")
def handle_git(user, request_repo):
    """Used internally by Git"""
    
    
    if not valid_repo.match(request_repo):
        subssh.errln("Illegal repository path '%s'" % request_repo)
        return 1    
    
    repo_name = request_repo.lstrip("/")
    
    # Transform virtual root
    real_repository_path = os.path.join(config.REPOSITORIES, repo_name)
    
    repo = Git(real_repository_path, user.username)
    
    # run requested command on the repository
    return repo.execute(user.username, user.cmd, git_bin=config.GIT_BIN)
    




def __appinit__():
    if subssh.to_bool(config.MANAGER_TOOLS):
        manager = GitManager(config.REPOSITORIES, 
                             urls=parse_url_configs(config.URLS),
                             webdir=config.WEBDIR )
        
        subssh.expose_instance(manager, prefix="git-")

