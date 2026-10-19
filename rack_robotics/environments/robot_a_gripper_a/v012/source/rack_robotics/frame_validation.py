"""Reject blank RTX captures; this is not a composition/photorealism verdict."""
from PIL import Image, ImageStat


def check_frame(path):
    with Image.open(path) as source:
        frame = source.convert('L')
        histogram = frame.histogram()
        pixels = frame.width*frame.height
        visible_fraction = sum(histogram[16:])/pixels
        variance = ImageStat.Stat(frame).var[0]
        if visible_fraction < .01 or variance < 1:
            raise ValueError(f'Blank/near-blank RTX capture: {path}; visible={visible_fraction:.6f}, variance={variance:.6f}')
        return {'visible_fraction_above_15': visible_fraction, 'luminance_variance': variance}
