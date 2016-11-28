#!/usr/bin/env python

import math
import cairo

w, h = 50, 200

def rounded_rect(context,w,h,r = 10, color=(255,255,255)):
    surface = cairo.ImageSurface (cairo.FORMAT_ARGB32, w, h)
    ctx = cairo.Context (surface)
    
    color = [v/255.0 for v in color]
    x = y = 0
    "Draw a rounded rectangle"
    #   A****BQ
    #  H      C
    #  *      *
    #  G      D
    #   F****E

    context.move_to(x+r,y)             # Move to A
    context.line_to(x+w-r,y)           # Straight line to B
    context.curve_to(x+w-r/2,   y,
                     x+w,   y+r/2,
                     x+w,   y+r)       # Curve to C, Control points are both at Q
    context.line_to(x+w,y+h-r)         # Move to D
    context.curve_to(x+w,   y+h-r/2,
                     x+w-r/2,   y+h,
                     x+w-r, y+h)       # Curve to E
    context.line_to(x+r,y+h)           # Line to F
    context.curve_to(x+r/2,     y+h,
                     x,     y+h-r/2,
                     x,     y+h-r)     # Curve to G
    context.line_to(x,y+r)             # Line to H
    context.curve_to(x,     y+r/2,
                     x+r/2,     y,
                     x+r,   y)         # Curve to A
    context.set_source_rgb (color[0], color[1], color[2]) # Solid color
    context.fill()
    return surface

surface = cairo.ImageSurface (cairo.FORMAT_ARGB32, w, h)
ctx = cairo.Context (surface)
rounded_rect(ctx, w, h, r=w/5.0)


ctx.set_source_rgb (0.3, 0.2, 0.5) # Solid color
ctx.fill()

# cx0, cy0, radius0, cx1, cy1, radius1
#grad = cairo.RadialGradient (0.5,0.5,0, 0.5,0.5, 0.1)
# stop location, r, g, b, a
#grad.add_color_stop_rgba (0.0, 1.0, 0.0, 1.0, 1.0)
#grad.add_color_stop_rgba (0.8, 1.0, 0.0, 1.0, 0.7)
#grad.add_color_stop_rgba (1.0, 1.0, 0.0, 1.0, 0.0)

#ctx.set_source(grad)
#ctx.arc(0.5, 0.5, 0.1, 0, 2*math.pi);
#ctx.close_path()
#ctx.fill()


surface.write_to_png ("test.png") # Output to PNG
