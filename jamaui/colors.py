# hildon colors

import gtk
import hildon

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
    font_desc = font_style.font_desc
    return font_desc

def get_color(logicalcolorname):
    settings = gtk.settings_get_default()
    color_style = gtk.rc_get_style_by_paths(settings, 'GtkButton', \
                                                'osso-logical-colors', gtk.Button)
    return color_style.lookup_color(logicalcolorname)

def font(name):
    return get_font_desc(name).to_string()


def color(name):
    return get_color('SecondaryTextColor').to_string()

import sys
current_module = sys.modules[__name__]

for fnt in logical_font_names:
    setattr(current_module, fnt, font(fnt))

for clr in logical_color_names:
    setattr(current_module, clr, color(clr))
