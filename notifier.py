import numpy as np
import cairo
import Image
import pygame

from latency_timer import LatencyTimer
from cairo_context import get_cairo_context

def text(text, color=(55, 55, 55)):
    context, h,w = get_cairo_context()

    color = [v / 255.0 for v in color]
    context.select_font_face("Ubuntu", cairo.FONT_SLANT_NORMAL,
                             cairo.FONT_WEIGHT_NORMAL)
    font_height_scale=0.05

    context.set_font_size(h*font_height_scale)

    context.translate(w/2,h/2)
    context.set_source_rgb(color[0], color[1], color[2])
    context.save()
    context.translate(0,0)
    context.rotate(np.pi*0.5)
    line = 1
    for t in text.splitlines():
        (x, y, width, height, dx, dy) = context.text_extents(t)
        context.move_to(-width/2, h*0.70+line*font_height_scale*h*1.1)
        #context.move_to(w/2-width/2, h/2+line*font_height_scale*h*1.1)
        context.show_text(t)
        line += 1
    context.restore()
    context.save()
    context.translate(0,0)
    context.rotate(np.pi*1.5)
    line = 1
    for t in text.splitlines():
        (x, y, width, height, dx, dy) = context.text_extents(t)
        context.move_to(-width/2, h*0.70+line*font_height_scale*h*1.1)
        #context.move_to(w/2-width/2, h/2+line*font_height_scale*h*1.1)
        context.show_text(t)
        line += 1
    context.restore()

class Notifier:
    thresh = 0.2

    def __init__(self):
        self.timer = LatencyTimer(4)
        self.fontsize = 48
        self.text = ""

    def update(self, **kwargs):
        print "updating notifier"
        # set a negative thresh to indicate no threshold to disappearance
        if "text" in kwargs:
            self.text = kwargs["text"]
            print "with text \"%s\""%self.text
        if "thresh" in kwargs:
            self.thresh = kwargs["thresh"]
        else:
            self.thresh = 0.5
        if "size" in kwargs:
            self.fontsize = kwargs["size"]
        else:
            self.fontsize = 48
        self.timer = LatencyTimer(self.thresh)

    def render(self):
        screen = pygame.display.get_surface()

        #print "Checking notifier timer with thresh %f"%self.timer.thresh
        if self.thresh<0 or not self.timer.check():
            text(self.text, color=(100,180,255))
