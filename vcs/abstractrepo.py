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
from ConfigParser import SafeConfigParser, NoOptionError

import subssh
from subssh import config


class InvalidRepository(IOError, subssh.UserException):
    pass

class BrokenRepository(IOError):
    pass


class InvalidPermissions(subssh.UserException):
    pass




class VCS(object):
    """
    Abstract class for creating VCS support
    """
    
    
    # Add some files/directories here which are required by the vcs
    required_by_valid_repo = None
    
    _permissions_section = "permissions"
    
    permdb_name="subssh_permissions"
    
    owner_filename="subssh_owners"
    
    known_permissions = "rw"
    
    
    prefix = ""
    suffix = ""
    
    
    def __init__(self, repo_path, requester):
        self.requester = requester
        self.repo_path = repo_path
        
        
        if not os.path.exists(self.repo_path):
            raise InvalidRepository("Repository '%s' does not exists!" 
                                    %  self.name )
        
        for path in self.required_by_valid_repo:
            if not os.path.exists(os.path.join(repo_path, path)):
                raise BrokenRepository("'%s' does not seem to be "
                                        "valid %s repository" % 
                                    (self.name, self.__class__.__name__))
                                
        
        self.permdb_filepath = os.path.join(repo_path, self.permdb_name)
        self.owner_filepath = os.path.join(repo_path, self.owner_filename)
        
        self.permdb = SafeConfigParser()
        self.permdb.read(self.permdb_filepath)
        
        if not self.permdb.has_section(self._permissions_section):
            self.permdb.add_section(self._permissions_section)
    
        self._owners = set()
        self._read_owners()
        
        
        if self.requester != config.ADMIN \
           and not self.is_owner(self.requester):
            raise InvalidPermissions("%s has no permissions to %s" %
                                     (self.requester, self))

        
    def __repr__(self):
        return "<%s %s>" % (self.__class__.__name__, self.name)
    
    
    
    def _read_owners(self):
        if os.path.exists(self.owner_filepath):
            f = open(self.owner_filepath, "r")
            for owner in f:
                self._owners.add(owner.strip())
            f.close()


    @property
    def name(self):
        name = os.path.basename(self.repo_path)
            
        if self.prefix and self.repo_path.startswith(self.suffix):
            name = name[len(self.suffix):]            
            
        if self.suffix and self.repo_path.endswith(self.suffix):
            name = name[:-len(self.suffix)]

            
        return name    
    
    
    @property
    def name_on_fs(self):
        return os.path.basename(self.repo_path)    
    
    
    def add_owner(self, username):
        self._owners.add(username)
        self.set_permissions(username, "rw")
        
    def get_owners(self):
        return sorted(list(self._owners))

    def is_owner(self, username):
        return username in self._owners


    def set_default_permissions(self, owner=None):
        if not owner:
            owner = self.requester
        
        
        self.remove_all_permissions()
        self.set_permissions("*", "r")
        
        self._owners = set([owner])
        self.set_permissions(owner, "rw")        
        
    def delete(self):
        """
        Deletes hole repository
        Cannot be undone!
        """
        shutil.rmtree(self.repo_path)


    def rename(self, new_repo_name):
        repo_dir = os.path.dirname(self.repo_path)
        new_path = os.path.join(repo_dir, new_repo_name.strip("/ "))
        
        shutil.move(self.repo_path, new_path)
        
        self.repo_path = new_path


    def remove_owner(self, username):
        if len(self._owners) == 1 and self.is_owner(username):
            raise InvalidPermissions("Cannot remove last owner %s" % username)
        self._owners.remove(username)


    def assert_permissions(self, permissions):
        for p in permissions:
            if p not in self.known_permissions:
                raise InvalidPermissions("Unknown permission %s" % p)
    
    

    def set_permissions(self, username, permissions):
        """Overrides previous permissions"""
        
        try:
            current_permissions = set(self.get_permissions(username))
        except InvalidPermissions:
            current_permissions = set()
        
        
        if permissions.startswith("+"):
            self.assert_permissions(permissions[1:])
            for perm in permissions[1:]:
                current_permissions.add(perm)
                
                
        elif permissions.startswith("-"):
            self.assert_permissions(permissions[1:])
            for perm in permissions[1:]:
                if perm in current_permissions:
                    current_permissions.remove(perm)
                    
        else:
            self.assert_permissions(permissions)
            current_permissions = set(permissions)
        
        
        
        if not current_permissions:
            self.remove_permissions(username)
        else:
            self.permdb.set(self._permissions_section, username, 
                            "".join(current_permissions))
    
    
    
    def get_all_permissions(self):
        """Return a list of tuples with (username, permissions)"""
        return sorted(self.permdb.items(self._permissions_section))

    def remove_all_permissions(self):
        for username, permissions in self.get_all_permissions():
            self.remove_permissions(username)
    
    def has_permissions(self, username, permissions):
        self.assert_permissions(permissions)
        permissions_got = set()
        
        try: # First get general permissions
            for p in self.permdb.get(self._permissions_section, "*"):
                permissions_got.add(p)
        except NoOptionError:
            pass
        
        try: # and user specific permissions
            for p in self.permdb.get(self._permissions_section, username):
                permissions_got.add(p)            
        except NoOptionError:
            pass
        
        # Iterate through required permissions
        for perm in permissions:
            # If even one is missing bail out!
            if perm not in permissions_got:
                return False
            
        # Everything was found
        return True
        
    def get_permissions(self, username):
        try:
            return self.permdb.get(self._permissions_section, 
                                   username)
        except NoOptionError:
            raise InvalidPermissions("No such user %s" % username)
    
    
    
    def remove_permissions(self, username):
        try:
            self.permdb.remove_option(self._permissions_section, username)
        except NoOptionError:
            raise InvalidPermissions("No such user %s" % username)
            

    
    def write_owners(self):
        f = open(self.owner_filepath, "w")
        for owner in self._owners:
            f.write(owner + "\n")
        f.close()        
        
    def write_permissions(self):
        f = open(self.permdb_filepath, "w")
        self.permdb.write(f)
        f.close()
    
    def save(self):
        self.write_owners()
        self.write_permissions()
        
