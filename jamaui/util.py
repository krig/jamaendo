import os
import simplejson

def string_in_file( filepath, string ):
    try:
        f = open( filepath, 'r' )
        found = f.read().find( string ) != -1
        f.close()
    except:
        found = False

    return found

def get_platform():
    if ( os.path.exists('/etc/osso_software_version') or
         os.path.exists('/proc/component_version') or
         string_in_file('/etc/issue', 'maemo') ):
        return 'maemo'
    else:
        return 'linux'

platform = get_platform()

def jsonprint(x):
    print simplejson.dumps(x, sort_keys=True, indent=4)

def find_resource(name):
    if os.path.isfile(os.path.join('data', name)):
        return os.path.join('data', name)
    elif os.path.isfile(os.path.join('/opt/jaemendo', name)):
        return os.path.join('/opt/jaemendo', name)
    elif os.path.isfile(os.path.join('/usr/share/jaemendo', name)):
        return os.path.join('/usr/share/jaemendo', name)
    else:
        return None

