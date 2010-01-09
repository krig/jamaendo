import logging
import gtk
import cairo

log = logging.getLogger(__name__)

def _hex_to_flt(r, g, b):
    return float(r)/255.0, float(g)/255.0, float(b)/255.0

# shows the current song position (looking a bit nicer than a default widget, hopefully)
class SongPosition(gtk.DrawingArea):
    WIDTH = 32.0
    HEIGHT = 16.0

    def __init__(self):
        gtk.DrawingArea.__init__(self)
        self.add_events(gtk.gdk.BUTTON_PRESS_MASK)
        self.connect('expose-event', self.on_expose)
        self.set_size_request(int(self.WIDTH), int(self.HEIGHT))
        self.pos = 0.0

        orange0 = _hex_to_flt(0xec, 0xac, 0x1f)
        orange1 = _hex_to_flt(0xea, 0x86, 0x1d)
        orange2 = _hex_to_flt(0xda, 0x76, 0x0d)
        orange3 = _hex_to_flt(0xd0, 0x70, 0x00)
        purple0 = _hex_to_flt(0x81, 0x3e, 0x82)
        purple1 = _hex_to_flt(0x56, 0x2d, 0x5a)

        lightclr = cairo.LinearGradient(0.0, 0.0, 0.0, self.HEIGHT)
        lightclr.add_color_stop_rgb(0.0, 1.0, 1.0, 1.0)
        lightclr.add_color_stop_rgb(0.1, *orange0)
        lightclr.add_color_stop_rgb(0.5, *orange1)
        lightclr.add_color_stop_rgb(0.5, *orange2)
        lightclr.add_color_stop_rgb(1.0, *orange3)

        darkclr = cairo.LinearGradient(0.0, 0.0, 0.0, self.HEIGHT)
        darkclr.add_color_stop_rgb(0.0, 0.5, 0.5, 0.5)
        darkclr.add_color_stop_rgb(0.5, 0.0, 0.0, 0.0)
        darkclr.add_color_stop_rgb(1.0, 0.25, 0.25, 0.25)

        markerclr = cairo.LinearGradient(0.0, 0.0, 0.0, self.HEIGHT)
        markerclr.add_color_stop_rgb(0.0, 1.0, 1.0, 1.0)
        markerclr.add_color_stop_rgb(0.5, 1.0, 1.0, 1.0)
        markerclr.add_color_stop_rgb(1.0, 1.0, 1.0, 1.0)

        self.lightclr = lightclr
        self.darkclr = darkclr
        self.markerclr = markerclr

    def on_expose(self, widget, event):
        context = self.window.cairo_create()
        context.rectangle(event.area.x, event.area.y,
            event.area.width, event.area.height)
        context.clip()
        self.draw(context)
        return True

    def draw(self, context):
        rect = self.get_allocation()

        lowx = rect.width*self.pos
        if lowx < 0.0:
            lowx = 0.0

        context.rectangle(0, 0, rect.width, rect.height)
        context.set_source(self.darkclr)
        context.fill()

        if lowx > 0.01:
            context.rectangle(0, 0, lowx, rect.height)
            context.set_source(self.lightclr)
            context.fill()

        context.rectangle(0, 0, rect.width, rect.height)
        context.set_source_rgb(0.3, 0.3, 0.3)
        context.stroke()

    def set_position(self, pos):
        if pos < 0.0:
            pos = 0.0
        elif pos > 1.0:
            pos = 1.0
        self.pos = pos
        self.queue_draw()
