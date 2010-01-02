import logging
import gtk
import cairo

log = logging.getLogger(__name__)

# shows the current song position (looking a bit nicer than a default widget, hopefully)
class SongPosition(gtk.DrawingArea):
    WIDTH = 8.0
    HEIGHT = 8.0

    def __init__(self):
        gtk.DrawingArea.__init__(self)
        self.connect('expose-event', self.on_expose)
        self.set_size_request(24, 8)
        self.pos = 0.0

        orange0 = self.hex_to_flt(0xec, 0xac, 0x1f)
        orange1 = self.hex_to_flt(0xea, 0x86, 0x1d, 0.25)
        purple0 = self.hex_to_flt(0x81, 0x3e, 0x82)
        purple1 = self.hex_to_flt(0x56, 0x2d, 0x5a, 0.25)

        lightclr = cairo.LinearGradient(0.0, 0.0, 0.0, self.HEIGHT)
        lightclr.add_color_stop_rgba(0.0, *purple1)
        lightclr.add_color_stop_rgba(1.0, *purple0)

        darkclr = cairo.LinearGradient(0.0, 0.0, 0.0, self.HEIGHT)
        darkclr.add_color_stop_rgba(0.0, 0.0, 0.0, 0.0, 0.0)
        darkclr.add_color_stop_rgba(1.0, 0.25, 0.25, 0.25, 1.0)

        markerclr = cairo.LinearGradient(0.0, 0.0, 0.0, self.HEIGHT)
        markerclr.add_color_stop_rgba(0.0, *orange1)
        markerclr.add_color_stop_rgba(0.5, *orange0)
        markerclr.add_color_stop_rgba(1.0, *orange0)

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

    #ecac1f - light orange
    #ea861d - dark orange

    #813e82 - light purple
    #562d5a - dark purple

    def hex_to_flt(self, r, g, b, a = 255.0):
        return float(r)/255.0, float(g)/255.0, float(b)/255.0, float(a)/255.0

    def draw(self, context):
        rect = self.get_allocation()


        #context.set_source_rgb(1.0, 0.5, 0.0)
        lowx = rect.width*self.pos - self.WIDTH*0.5
        hix = rect.width*self.pos + self.WIDTH*0.5

        if lowx < 0.0:
            lowx = 0.0
            hix = self.WIDTH
        elif hix > rect.width:
            lowx = rect.width - self.WIDTH
            hix = rect.width

        if lowx > 0.01:
            context.rectangle(0, 0, lowx, rect.height)
            context.set_source(self.lightclr)
            context.fill()

        if hix < rect.width-0.01:
            context.rectangle(hix, 0, rect.width-hix, rect.height)
            context.set_source(self.darkclr)
            context.fill()

        context.rectangle(lowx, 0, self.WIDTH, rect.height)
        context.set_source(self.markerclr)
        context.fill()

    def set_position(self, pos):
        assert 0 <= pos <= 1
        self.pos = pos
        self.invalidate()

    def invalidate(self):
        self.queue_draw()
