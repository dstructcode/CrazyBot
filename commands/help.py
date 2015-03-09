import pkgutil

def get_help():
    modules = pkgutil.iter_modules(path=["commands"])
    modules_str = ""
    for loader, mod_name, ispkg in modules:
        modules_str = modules_str + "." + mod_name + " "
    modules_str = ''.join(modules_str.split('.help '))
    return "Commands: %s-- %s" % (modules_str, ".help <command> for more info")
