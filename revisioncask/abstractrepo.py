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
from subssh.dirtools import create_required_directories_or_die


class InvalidRepository(IOError, subssh.UserException):
    pass

class BrokenRepository(IOError):
    pass


class InvalidPermissions(subssh.UserException):
    pass


def vcs_init(config):
    create_required_directories_or_die((config.REPOSITORIES, config.HOOKS_DIR))



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


    admin_name = "admin"


    prefix = ""
    suffix = ""


    def __init__(self, repo_path, requester, create=False):
        self.requester = requester
        self.repo_path = repo_path
        self._owners = set()

        if create:
            self._init_new()
        else:
            self._init_existing()


    def _init_new(self):
        """
        Creates new repository to the path.
        Creates necessary directories.
        Sets initial permissions.
        """
        self._init_repository_location()
        self._create_repository_files()
        self._load_permissions()
        # When creating new repository the requester is always the owner
        self.add_owner(self.requester)
        self.save()

    def _init_existing(self):
        """
        1. Checks that given path is really a repository.
        2. Loads permissions
        3. Checks the permissions
        """
        self._assert_valid_repository()
        self._load_permissions()
        self._assert_can_manage()

    def _assert_valid_repository(self):
        """
        Lets do some assertions that this really is repository directory that
        we are expecting 
        """
        if not os.path.exists(self.repo_path):
            raise InvalidRepository("Repository '%s' does not exists!" % 
                                    self.name )

        for path in self.required_by_valid_repo:
            if not os.path.exists(os.path.join(self.repo_path, path)):
                raise BrokenRepository("'%s' does not seem to be "
                                        "valid %s repository" %
                                    (self.name, self.__class__.__name__))

    def _assert_can_manage(self):
        if self.requester != self.admin_name \
           and not self.is_owner(self.requester):
            raise InvalidPermissions("%s has no permissions to %s" %
                                     (self.requester, self))

    def _create_repository_files(self):
        raise NotImplementedError



    def _init_repository_location(self):
        """
        Run before _create_repository

        Setups path to be initable for new repository.  Creates directories if
        they do not exist.  Raises InvalidRepository if the leaf is not empty.
        """
        if not os.path.exists(self.repo_path):
            os.makedirs(self.repo_path)

        elif len(os.listdir(self.repo_path)) != 0:
            raise InvalidRepository("Cannot create new repository. "
                          "The target %s is not empty" % self.repo_path)



    def _load_permissions(self):

        self.permdb_filepath = os.path.join(self.repo_path, self.permdb_name)
        self.owner_filepath = os.path.join(self.repo_path, self.owner_filename)

        self.permdb = SafeConfigParser()
        self.permdb.read(self.permdb_filepath)

        if not self.permdb.has_section(self._permissions_section):
            self.permdb.add_section(self._permissions_section)

        self._read_owners()



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
        # Owner will have all permissions to the repository
        self.set_permissions(username, self.known_permissions)

    def get_owners(self):
        return sorted(list(self._owners))

    def is_owner(self, username):
        return username in self._owners



    def delete(self):
        """
        Deletes whole repository
        Cannot be undone!
        """
        # TODO: Should this in the repository manager?
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


        # Adding permissions
        if permissions.startswith("+"):
            self.assert_permissions(permissions[1:])
            for perm in permissions[1:]:
                current_permissions.add(perm)


        # Removing permissions
        elif permissions.startswith("-"):
            self.assert_permissions(permissions[1:])
            for perm in permissions[1:]:
                if perm in current_permissions:
                    current_permissions.remove(perm)

        # Set permissions, overrides previous one
        else:
            self.assert_permissions(permissions)
            current_permissions = set(permissions)



        # Remove user name from the permissions file if user has no permissions
        if not current_permissions:
            self.remove_permissions(username)
        else:
            self.permdb.set(self._permissions_section, username,
                            "".join(current_permissions))



    def get_all_permissions(self):
        """Return a list of tuples with (username, permissions)"""
        return sorted(self.permdb.items(self._permissions_section))

    # TODO: make private
    def remove_all_permissions(self):
        for username, permissions in self.get_all_permissions():
            self.remove_permissions(username)

    def reset_permissions_to(self, username):
        """
        Makes username the only owner and permission owner
        """
        self.remove_all_permissions()
        self._owners = set()
        self.add_owner(username)



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

    def set_hooks(self, hooks):
        raise NotImplementedError

