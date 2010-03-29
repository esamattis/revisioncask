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
import shutil
from string import Template


import subssh


from subssh import config
from abstractrepo import InvalidPermissions, InvalidRepository





def parse_url_configs(url_configs):
    urls = []
    for url_config in url_configs.split("\n"):
        urls.append( tuple(url_config.split("|")) )
    return urls
        
        
def format_list(iterable, sep=", "):
    return sep.join(iterable).strip(sep)

class RepoManager(object):
    
    suffix = ""
    prefix = ""
    klass = None
    
    def __init__(self, path_to_repos, webdir="", urls=[]):
        self.path_to_repos = path_to_repos
        self.urls = urls
        self.webdir = webdir
        
        if self.webdir and not os.path.exists(self.webdir):
            os.makedirs(self.webdir)
        
        
        if not os.path.exists(self.path_to_repos):
            os.makedirs(self.path_to_repos)
        

                
        
    
    def real(self, repo_name):
        """
        Return real path of the repository
        """
        return os.path.join(self.path_to_repos, 
                            self.prefix + repo_name + self.suffix)
    
    def get_repo_object(self, username, repo_name):
        return self.klass(self.real(repo_name), username)
    
    
    @subssh.exposable_as()
    def fork(self, user, repo_name, fork_name):
        """
        Fork a reposotory
        
        Make a copy of the repository for yourself.
        
        usage: $cmd <repo name> <fork name>
        
        """
        repo = self.get_repo_object(config.ADMIN, repo_name)
        if not repo.has_permissions(user.username, "r"):
            raise InvalidPermissions("You need read permissions for forking")
        
        fork_path = os.path.join(self.path_to_repos, self.real(fork_name))
        
        if os.path.exists(fork_path):
            raise InvalidRepository("Repository '%s' already exists."
                                     % repo_name)
        
        shutil.copytree(repo.repo_path, fork_path)
        
        
        repo = self.klass(fork_path, config.ADMIN)
        
        
        self._set_default_permissions(fork_path, user.username)
        
        subssh.writeln("\n\n Forked repository '%s' to '%s' \n" 
                       % (repo_name, fork_name))
        self.info(user, fork_name)


    @subssh.exposable_as()
    def web(self, user, repo_name, action=""):
        """
        Enable anonymous webview.
        
        usage: $cmd <repo name> <enable|disable>
        """
        repo = self.get_repo_object(user.username, repo_name)
        webpath = os.path.join(self.webdir, repo.name_on_fs)
        
        if action == "enable":
            if not os.path.exists(webpath):
                os.symlink(repo.repo_path, webpath)
        elif action == "disable":
            if os.path.exists(webpath):
                os.remove(webpath)
        else:
            raise subssh.InvalidArguments("Second argument must be 'enable' "
                                         "or 'disable'")
    
    
    @subssh.exposable_as()
    def ls(self, user, action=""):
        """
        List repositories.
        
        usage: $cmd [mine|all]
        """
        repos = []
        
        
        request_user = user.username
        try:
            if action == 'all':
                request_user = config.ADMIN
        except IndexError:
            pass
        
        
        for repo_in_fs in os.listdir(self.path_to_repos):
            try:
                repo = self.klass(os.path.join(self.path_to_repos, 
                                               repo_in_fs),
                                  request_user)
            except InvalidPermissions:
                continue
            except InvalidRepository:
                continue
            else:
                repos.append(repo)
        
        for repo in sorted(repos):
            subssh.writeln(repo.name)
            
            
    @subssh.exposable_as()
    def info(self, user, repo_name):
        """
        Show information about repository.
        
        Shows repository paths, owner and permissions.
        
        usage: $cmd <repo name>
        """
        repo = self.get_repo_object(config.ADMIN, repo_name)
        
        
        subssh.writeln()
        subssh.writeln("Access:")
        for url_name, url_tmpl in self.urls:
            url = Template(url_tmpl).substitute(name=repo.name, 
                                                name_on_fs=repo.name_on_fs,
                                                hostname=config.DISPLAY_HOSTNAME,
                                                hostusername=subssh.hostusername(),)
            subssh.writeln("    %s: %s" %(url_name, url) )
        
        
        subssh.writeln()
        subssh.writeln("Owners: %s" % format_list(repo.get_owners()))
        subssh.writeln()
        
        subssh.writeln("Permissions:")
        for username, perm in repo.get_all_permissions():
            subssh.writeln("    %s = %s" %(username, perm) )
        
        
    
    
    
    @subssh.exposable_as()
    def delete(self, user, repo_name):
        """
        Delete repository.
        
        usage: $cmd <repo name>
        """
        repo = self.get_repo_object(user.username, repo_name)
        repo.delete()
    
    @subssh.exposable_as()
    def add_owner(self, user, repo_name, username):
        """
        Add owner to repository.
        
        usage: $cmd <repo name> <username>
        """
        repo = self.get_repo_object(user.username, repo_name)
        repo.add_owner(username)
        repo.save()
        
        
    @subssh.exposable_as()
    def remove_owner(self, user, repo_name, username):
        """
        Remove owner from repository.
        
        usage: $cmd <repo name> <username>
        """
        repo = self.get_repo_object(user.username, repo_name)
        repo.remove_owner(username)
        repo.save()    
    
    
    
    @subssh.exposable_as()
    def rename(self, user, repo_name, new_name):
        """
        Rename repository.
        
        usage: $cmd <repo name> <new repo name>
        """
        repo = self.get_repo_object(user.username, repo_name)
        repo.rename(new_name)        
        

    @subssh.exposable_as()
    def set_permissions(self, user, username, permissions, repo_name):
        """
        Set read/write permissions to repository.
        
        usage: $cmd <username> <permissions> <repo name>
        
        Permissions can be 'r', 'w', or 'rw'
        
        Eg. $cmd myfriend rw myrepository
        
        Only owners can change permissions. Owners can also add and remove
        other owners. 
        
        """
        repo = self.get_repo_object(user.username, repo_name)
        repo.set_permissions(username, permissions)
        repo.save()
        
        
    def _set_default_permissions(self, repo_path, owner):
        """
        Set default permission to a repository.
        
        Overrides previous permissions if any
        """

        f = open(os.path.join(repo_path, self.klass.owner_filename), "w")
        f.write(owner)
        f.close()        
        
        repo = self.klass(repo_path, owner)
        repo.set_default_permissions()
        repo.save()        
        
        
    @subssh.exposable_as()
    def init(self, user, repo_name):
        """
        Create new repository.
        
        usage: $cmd <repository name>
        """
         
        if not subssh.safe_chars_only_pat.match(repo_name):
            subssh.errln("Bad repository name. Allowed characters: %s (regexp)" 
                        % subssh.safe_chars)
            return 1                
        
        repo_path = self.real(repo_name)
        if os.path.exists(repo_path):
            raise InvalidRepository("Repository '%s' already exists."
                                     % repo_name)
    
        if not os.path.exists(repo_path):
            os.makedirs(repo_path)
            
        self.create_repository(repo_path, user.username)
        
        self._set_default_permissions(repo_path, user.username)
        
        subssh.writeln("\n\n Created new repository '%s' \n" % repo_name)
        
        self.info(user, repo_name)
    

    def create_repository(self, repo_path, username):
        raise NotImplementedError
    