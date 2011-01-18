'''
Created on Apr 6, 2010

@author: epeli
'''




import os
import sys
import re
from ConfigParser import SafeConfigParser
from optparse import OptionParser

import subssh

from abstractrepo import VCS
from abstractrepo import InvalidPermissions
from repomanager import RepoManager


class config:
    HG_BIN = "hg"

    REPOSITORIES = os.path.join( os.environ["HOME"],
                                 ".subssh", "repos", "hg" )


    MANAGER_TOOLS = "true"


    URL_RW =  "ssh://$hostusername@$hostname/$name_on_fs"
    URL_HTTP_CLONE =  "http://$hostname/repo/$name_on_fs"
    URL_WEB_VIEW =  "http://$hostname/viewgit/?a=summary&p=$name_on_fs"

    WEB_DIR = os.path.join( os.environ["HOME"], "repos", "webhg" )


hg_manager = None

class Mercurial(VCS):

    required_by_valid_repo  = (".hg",)



    _permissions_section = "subssh.permissions"

    owner_filename=".hg/hgrc"

    permdb_name=owner_filename

    owner_sep = ", "


    def _read_owners(self):
        if self.permdb.has_section("web"):
            owners_str = self.permdb.get("web", "contact")
            for owner in owners_str.split(self.owner_sep):
                self._owners.add(owner)
        else:
            self.permdb.add_section("web")



    def write_owners(self):
        sorted_owners = sorted(self._owners)
        owners_str = self.owner_sep.join(sorted_owners).strip(self.owner_sep)
        self.permdb.set("web", "contact", owners_str )




    def set_description(self, description):
        self.permdb.set("web", "description", description)



class MercurialManager(RepoManager):
    klass = Mercurial


    @subssh.exposable_as()
    def set_description(self, user, repo_name, *description):
        """
        Set description for web interface.

        usage: $cmd <repo name> <description>

        """
        repo = self.get_repo_object(user.username, repo_name)
        repo.set_description(" ".join(description))
        repo.save()


    def create_repository(self, path, owner):
        from mercurial import ui, hg
        hg_repo = hg.repository(ui.ui(), path, create=True)

        hgrc = SafeConfigParser()
        hgrc_filepath = os.path.join(hg_repo.path, "hgrc")

        hgrc.read(hgrc_filepath)


        if not hgrc.has_section("hooks"):
            hgrc.add_section("hooks")


        # http://hgbook.red-bean.com/read/handling-repository-events-with-hooks.html#sec:hook:prechangegroup
        # http://hgbook.red-bean.com/read/handling-repository-events-with-hooks.html#sec:hook:pretxnchangegroup
        hgrc.set("hooks", "prechangegroup.subssh.permissions",
                 "python:subssh.app.vcs.hg.permissions_hook")

        f = open(hgrc_filepath, "w")
        hgrc.write(f)
        f.close()









parser = OptionParser()


parser.add_option('-R', '--repository', dest='repository')
parser.add_option("--stdio", action="store_true", dest='stdio' )



valid_repo = re.compile(r"^[%s]+$" % subssh.safe_chars)

@subssh.no_interactive
@subssh.expose_as("hg")
def hg_handle(user, *args):
    """Used internally by Mercurial"""


    options, args = parser.parse_args(list(args))

    if args[0] == 'serve':
        return hg_serve(user, options, args)
    elif args[0] == 'init':
        return hg_init(user, options, args)
    else:
        raise subssh.InvalidArguments("Bad Mercurial command")



def hg_serve(user, options, args):
    if not options.repository:
        raise subssh.InvalidArguments("Repository is missing")
    if not options.stdio:
        raise subssh.InvalidArguments("'--stdio' is missing")


    if not valid_repo.match(options.repository):
        subssh.errln("Illegal repository path '%s'" % options.repository)
        return 1

    repo_name = options.repository.lstrip("/")

    # Transform virtual root
    real_repository_path = os.path.join(config.REPOSITORIES, repo_name)

    repo = Mercurial(real_repository_path, subssh.config.ADMIN)

    if not repo.has_permissions(user.username, "r"):
        raise InvalidPermissions("%s has no read permissions to %s"
                                 %(user.username, options.repository))

    from mercurial.dispatch import dispatch
    return dispatch(['-R', repo.repo_path, 'serve', '--stdio'])



def hg_init(user, options, args):
    return hg_manager.init(user, args[1])

def permissions_hook(ui=None, repo=None, **kwargs):

    user = subssh.get_user()

    # TODO: upper = os.path.dirname(repo.path) ?
    upper = "/".join(repo.path.split("/")[:-1])

    repo_subssh = Mercurial(upper, subssh.config.ADMIN)

    if not repo_subssh.has_permissions(user.username, "w"):
        from mercurial.util import Abort
        raise Abort('%s has no write permissions to %s' %
                          (user.username, repo_subssh.name ))




def appinit():
    if subssh.to_bool(config.MANAGER_TOOLS):
        global hg_manager
        hg_manager = MercurialManager(config.REPOSITORIES,
                         web_repos_path=config.WEB_DIR,
                         urls={'rw': config.URL_RW,
                               'anonymous_read': config.URL_HTTP_CLONE,
                               'webview': config.URL_WEB_VIEW},
                         )

        subssh.expose_instance(hg_manager, prefix="hg-")

