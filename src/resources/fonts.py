from PIL import ImageFont


def get_font(size: int):
    return ImageFont.truetype("resources/fonts/gg_sans.ttf", size)
