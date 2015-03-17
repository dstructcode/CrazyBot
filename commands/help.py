import os
import pkgutil

path = os.path.dirname(os.path.abspath(__file__))

def get_help():
    modules = pkgutil.iter_modules(path=[path])
    modules_str = ""
    for loader, mod_name, ispkg in modules:
        modules_str = modules_str + "." + mod_name + " "
    modules_str = ''.join(modules_str.split('.help ')).rstrip()
    return "Commands: %s -- %s" % (modules_str, ".help <command> for more info")
