# Media player controls
#dbus-send --print-reply --dest=com.nokia.mediaplayer /com/nokia/mediaplayer com.nokia.mediaplayer.mime_open string:"file:///$1"
#dbus-send --dest=com.nokia.osso_media_server /com/nokia/osso_media_server com.nokia.osso_media_server.music.pause
import dbus

