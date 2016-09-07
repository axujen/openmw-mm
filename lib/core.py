# Core functions used in both CLI and GUI
# Rule of thumb, imports from this projects modules should be done inside the
# functions that call them.
import os
import sys
import shutil
import platform


def get_modsource(path):
    from modsource import ModSourceDir, ModSourceArchive
    """This will return a proper ModSource subclass for a given source.
    If path is a directory it returns ModSourceDir() class otherwise it returns
    ModSourceArchive()

    :path: (str) Absolute path to the soruce.
    :returns: (ModSource subclass)
    """
    if os.path.isdir(path):
        return ModSourceDir(path)
    else:
        return ModSourceArchive(path)


def get_full_path(path):
    """Return the full expanded path of :path:.

    :path: (str) Path to expand.
    :returns: (str) Expanded path.
    """

    # Expand env variables.
    path = os.path.expandvars(path)
    # Expand user (~)
    path = os.path.expanduser(path)
    # Get the absolute path
    path = os.path.abspath(path)
    # normalize
    path = os.path.normpath(path)
    path = os.path.normcase(path)

    return path


# TODO: Make this function safer.
def rm_mod_dir(mod_dir):
    """Delete a mod directory

    :mod_dir: (str) Path to the mod directory to be deleted.
    :raises: (ValueError)
    """
    if not os.path.exists(mod_dir):
        raise ValueError("'%s' does not exist." % mod_dir)
    if not os.path.isdir(mod_dir):
        raise ValueError("'%s' is not a directory." % mod_dir)

    shutil.rmtree(mod_dir)


def get_plugins(cfg):
    """Get all plugins enabled and disabled plugins.
    Note: this wont return orphaned plugins since they can't have a plugin object.

    :cfg: (ConfigFile) openmw.cfg object.
    :returns: (list) list of all plugin objects referenced in openmw.cfg.
    """
    mods = cfg.get_mods()
    plugins = []
    for mod in mods:
        if not mod.is_installed():
            continue

        for plugin in mod.get_plugins():
            plugins.append(plugin)

    return plugins


def get_enabled_plugins(cfg):
    """Get a list of enabled plugins sorted by load order.

    :cfg: (ConfigFile) openmw.cfg object.
    :returns: (list) List of enabled plugin objects sorted by load order.
    """
    plugins = []
    for plugin in get_plugins(cfg):
        if plugin.is_enabled():
            plugins.append(plugin)

    return sorted(plugins, key=lambda plugin: plugin.get_order())


def get_disabled_plugins(cfg):
    """Get a list of plugins that are installed but not enabled.

    :cfg: (ConfigFile) openmw.cfg object.
    :returns: (list) List of disabled plugin objects
    """
    plugins = []
    for plugin in get_plugins(cfg):
        if not plugin.is_enabled():
            plugins.append(plugin)

    return plugins


def get_orphaned_plugins(cfg):
    """Get a list of plugins that have entries in openmw.cfg but have no parent mod.

    :cfg: (ConfigFile) openmw.cfg object
    :returns: (list)
    """

    installed_plugins = [p.get_name() for p in get_plugins(cfg)]
    plugins = [e.get_value() for e in cfg.find_key("content")]
    orphaned = []

    for plugin in plugins:
        if plugin not in installed_plugins:
            orphaned.append(plugin)

    return orphaned


def find_plugin(cfg, plugin_name):
    """Find an installed plugin by name

    :plugin_name: (str) Plugin name
    :returns: (OmwPlugin or None)
    """
    mods = cfg.get_mods()
    for mod in mods:
        plugins = mod.get_plugins()
        if not plugins:
            continue
        for plugin in plugins:
            if plugin.get_name() == plugin_name:
                return plugin

    return None


def get_base_dir():
    """Return the path of the base directory where the script is located.
    This should be the directory where lib exists.

    :return: (str) Path
    """
    # os.path.realpath to resolve symlinks
    return os.path.realpath(sys.path[0])


# This function exists because whoever wrote the libarchive module
# didn't take into consideration cross-platform support for libarchive.
# so im shipping pre-compiled libarchive libraries and manually setting
# the PATH env variable to end all problems with libarchive.
# TODO: Test the rest of the platforms if they are working
# So far tested linux64 and windows32
def setup_libarchive():
    """Setup the path variable to point to the bundled libarchive libs."""
    OS = platform.system()
    ARCH = platform.architecture()[0]
    libdir = os.path.join(get_base_dir(), "lib/bin/%s/%s" % (OS, ARCH))
    curdir = os.getcwd()
    # For some reason OSX won't load the library properly if the script isn't
    # in the lib dir, this is a hack untill to fix the probem untill i get to
    # the bottom of this.
    try:
        os.chdir(libdir)

        # Put my libs in the start of PATH so system-wide libs take precedence?
        # May put it in the end if issues arise.
        os.environ["PATH"] = os.pathsep.join((libdir, os.environ["PATH"]))
        import libarchive.public as libarchive
        return libarchive
    finally:
        os.chdir(curdir)
