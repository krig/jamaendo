import os

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
