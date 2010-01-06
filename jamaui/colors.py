# hildon colors

import gtk
try:
    import hildon
    _using_helldon = False
except:
    import helldon as hildon
    _using_helldon = True

# See the Fremantle Master Layout Guide for more information:
# http://tinyurl.com/fremantle-master-layout-guide

logical_font_names = (
    'SystemFont',
    'EmpSystemFont',
    'SmallSystemFont', # Used for secondary text in buttons/TreeViews
    'EmpSmallSystemFont',
    'LargeSystemFont', # Used for empty TreeView text
    'X-LargeSystemFont',
    'XX-LargeSystemFont',
    'XXX-LargeSystemFont',
    'HomeSystemFont',
)

logical_color_names = (
    'ButtonTextColor',
    'ButtonTextPressedColor',
    'ButtonTextDisabledColor',
    'ActiveTextColor', # Used for Button values, etc..
    'SecondaryTextColor', # Used for additional/secondary information
)

def get_font_desc(logicalfontname):
    settings = gtk.settings_get_default()
    font_style = gtk.rc_get_style_by_paths(settings, logicalfontname, \
                                               None, None)
    if not font_style:
        font_style = gtk.rc_get_style_by_paths(settings,
                                               'GtkButton', 'GtkButton', gtk.Button)

    font_desc = font_style.font_desc
    return font_desc

def get_color(logicalcolorname):
    settings = gtk.settings_get_default()
    color_style = gtk.rc_get_style_by_paths(settings, 'GtkButton', \
                                                'osso-logical-colors', gtk.Button)

    if not color_style:
        font_style = gtk.rc_get_style_by_paths(settings,
                                               'GtkButton', 'GtkButton', gtk.Button)
    return color_style.lookup_color(logicalcolorname)

if _using_helldon:
    def font(name):
        return "normal"
else:
    def font(name):
        return get_font_desc(name).to_string()

if _using_helldon:
    def color(name):
        return "#333333"
else:
    def color(name):
        return get_color(name).to_string()

import sys
current_module = sys.modules[__name__]

def mk_font_fun(name):
    def inner():
        return font(name)
    return inner

for fnt in logical_font_names:
    setattr(current_module, fnt.replace('-', ''), mk_font_fun(fnt))

for clr in logical_color_names:
    setattr(current_module, clr, lambda: color(clr))
