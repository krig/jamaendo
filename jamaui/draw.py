import gtk
import pango

def text_box_centered(ctx, widget, w_width, w_height, text, font_desc=None):
    style = widget.rc_get_style()
    text_color = style.text[gtk.STATE_PRELIGHT]
    red, green, blue = text_color.red, text_color.green, text_color.blue
    text_color = [float(x)/65535. for x in (red, green, blue)]
    text_color.append(.5)

    if font_desc is None:
        font_desc = style.font_desc
        font_desc.set_size(14*pango.SCALE)

    pango_context = widget.create_pango_context()
    layout = pango.Layout(pango_context)
    layout.set_font_description(font_desc)
    layout.set_text(text)
    width, height = layout.get_pixel_size()

    ctx.move_to(w_width/2-width/2, w_height/2-height/2)
    ctx.set_source_rgba(*text_color)
    ctx.show_layout(layout)
