import pygame
import cairo

def get_cairo_context():
    screen = pygame.display.get_surface()
    w = screen.get_width()
    h = screen.get_height()

    pixels = pygame.surfarray.pixels2d(screen)
    #
    #    # Set up a Cairo surface using the same memory block and the same pixel
    #    # format (Cairo's RGB24 format means that the pixels are stored as
    #    # 0x00rrggbb; i.e. only 24 bits are used and the upper 16 are 0).
    cairo_surface = cairo.ImageSurface.create_for_data(pixels.data, cairo.FORMAT_RGB24, w, h)

    #data = np.full(w * h * 4, 0, dtype=np.int8)
    #cairo_surface = cairo.ImageSurface.create_for_data(
    #    data, cairo.FORMAT_ARGB32, w, h, w * 4)

    context = cairo.Context(cairo_surface)

    return context, h, w