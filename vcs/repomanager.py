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

import subssh


from subssh import config
from abstractrepo import InvalidPermissions, InvalidRepository






        
def format_list(iterable, sep=", "):
    return sep.join(iterable).strip(sep)

class RepoManager(object):
    
    klass = None
    
    def __init__(self, repos_path, web_repos_path=None, urls={}):
        self.path_to_repos = repos_path
        if web_repos_path:
            self.web_repos_path = web_repos_path
        else:
            self.web_repos_path = os.path.join(self.path_to_repos, "web")
        self.urls = urls
        
        if self.web_repos_path and not os.path.exists(self.web_repos_path):
            os.makedirs(self.web_repos_path)
        
        
        if not os.path.exists(self.path_to_repos):
            os.makedirs(self.path_to_repos)
        
        

        
            
        
    
    def real_path(self, repo_name):
        """
        Return real path of the repository
        """
        return os.path.join(self.path_to_repos, 
                            self.klass.prefix + repo_name + self.klass.suffix)
    
    def real_name(self, repo_name):
        """
        Real name on fs
        """
        return os.path.basename(self.real_path(repo_name))
    
    
    def get_repo_object(self, username, repo_name):
        return self.klass(self.real_path(repo_name), username)
    
    
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
        
        fork_path = os.path.join(self.path_to_repos, self.real_path(fork_name))
        
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
    def web_enable(self, user, repo_name, ):
        """
        Enable anonymous webview.
        
        usage: $cmd <repo name>
        """
        repo = self.get_repo_object(user.username, repo_name)
        if not repo.has_permissions('*', 'r'):
            raise InvalidPermissions("Cannot enable web view for private "
                                     "repository. Add read permission for "
                                     "'*' first")
        
        webrepopath = os.path.join(self.web_repos_path, repo.name_on_fs)

        if not os.path.exists(webrepopath):
            os.symlink(repo.repo_path, webrepopath)


    
    @subssh.exposable_as()
    def web_disable(self, user, repo_name, ):
        """
        Enable anonymous webview.
        
        usage: $cmd <repo name>
        """
        repo = self.get_repo_object(user.username, repo_name)
        webrepopath = os.path.join(self.web_repos_path, repo.name_on_fs)
        
        if os.path.exists(webrepopath):
            os.remove(webrepopath)


    
    
    def is_web_enabled(self, repo):
        webpath = os.path.join(self.web_repos_path, repo.name_on_fs)
        return os.path.exists(webpath)

        
    
    @subssh.exposable_as()
    def ls(self, user, action=""):
        """
        List repositories.
        
        usage: $cmd [mine]
        """
        repos = []
        
        for repo_in_fs in os.listdir(self.path_to_repos):
            try:
                repo = self.klass(os.path.join(self.path_to_repos, 
                                               repo_in_fs),
                                  config.ADMIN)
            except InvalidRepository:
                continue
            else:
                repos.append(repo)
        
        if action == "mine":
            repos = [repo for repo in repos if repo.is_owner(user.username)]
        elif not action:
            repos = [repo for repo in repos if repo.is_owner(user.username) 
                     and repo.has_permissions(user.username, 'r')]
        elif action:
            raise subssh.InvalidArguments("Unknown action '%s'" % action)
        
        
        
        
        for repo in sorted(repos, lambda a, b: cmp(a.name, b.name)):
            subssh.writeln(repo.name)
                
            
            
            
            
    
    def viewable_urls(self, username, repo):
        viewable_urls = {}
        
        for name, url_tmp in self.urls.items():
            viewable_urls[name] = subssh.expand_subssh_vars(url_tmp, 
                                                name_on_fs=repo.name_on_fs)        
        
        
        if (not repo.has_permissions(username, 'r') 
            and self.urls.has_key('rw')):
            
                del viewable_urls['rw']
        
        if not self.is_web_enabled(repo):
            
            if self.urls.has_key('anonymous_read'):
                del viewable_urls['anonymous_read']
                
            if self.urls.has_key('webview'):
                del viewable_urls['webview']
                
        return viewable_urls      
        
                    
            
            
    @subssh.exposable_as()
    def info(self, user, repo_name):
        """
        Show information about repository.
        
        Shows repository paths, owner and permissions.
        
        usage: $cmd <repo name>
        """
        repo = self.get_repo_object(config.ADMIN, repo_name)
        
        
        subssh.writeln()
        subssh.writeln("Owners: %s" % format_list(repo.get_owners()))
        subssh.writeln()
        
        subssh.writeln("Permissions:")
        for username, perm in repo.get_all_permissions():
            subssh.writeln("%s = %s" %(username, perm), indent=4 )
        
        subssh.writeln()
        
        if self.is_web_enabled(repo):
            subssh.writeln("Anonymous web view is enabled")
        else:
            subssh.writeln("Anonymous web view is disabled")
    
        subssh.writeln()
        subssh.writeln("Access:")
        
        urls = self.viewable_urls(user.username, repo)
        
        try:
            subssh.writeln("Read/Write %s" % urls['rw'], indent=4)
        except KeyError:
            pass
        try:
            subssh.writeln("Anonymous read %s" % urls['anonymous_read'], indent=4)
        except KeyError:
            pass
        try:
            subssh.writeln("Web view %s" % urls['webview'], indent=4)
        except KeyError:
            pass               
        subssh.writeln()
    
    
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
        
        usage: $cmd <username> <+/-permissions> <repo name>
        
        Permissions can be 'r', 'w', or 'rw'.
        
        Eg. $cmd myfriend r myrepository
            $cmd myanotherfriend +w myrepository
        
        Only owners can change permissions. Owners can also add and remove
        other owners. 
        
        """
        repo = self.get_repo_object(user.username, repo_name)
        repo.set_permissions(username, permissions)
        if not repo.has_permissions('*', 'r') and self.is_web_enabled(repo):
            self.web_disable(user, repo_name)
            subssh.errln("Note: Web view disabled")
        repo.save()
        
        
    def _set_default_permissions(self, repo_path, owner):
        """
        Set default permission to a repository.
        
        Overrides previous permissions if any
        """

        
        repo = self.klass(repo_path, subssh.config.ADMIN)
        repo.set_default_permissions(owner)
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
        
        repo_path = self.real_path(repo_name)
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
    

    