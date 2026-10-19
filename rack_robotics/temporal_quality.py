"""Frame-level temporal screening, not automatic visual acceptance."""
import math
from PIL import ImageChops, ImageStat


def frame_metrics(frame, previous=None):
    gray = frame.convert('L')
    pixels = gray.width * gray.height
    hist = gray.histogram()
    stat = ImageStat.Stat(gray)
    result = {'mean_luminance': stat.mean[0], 'luminance_variance': stat.var[0],
              'visible_fraction_above_15': sum(hist[16:]) / pixels,
              'near_white_fraction_above_245': sum(hist[246:]) / pixels}
    if previous is not None:
        difference = ImageChops.difference(gray, previous.convert('L'))
        result.update(mean_absolute_change=ImageStat.Stat(difference).mean[0],
                      changed_fraction_above_40=sum(difference.histogram()[41:]) / pixels)
    else:
        result.update(mean_absolute_change=0., changed_fraction_above_40=0.)
    return result


def screen_flags(rows, camera_cuts=()):
    """Review flags only. Fast legitimate camera/occlusion motion can trigger them."""
    cuts = set(camera_cuts)
    flags = []
    for index, row in enumerate(rows):
        reasons = []
        if row['visible_fraction_above_15'] < .01 or row['luminance_variance'] < 1:
            reasons.append('blank_or_nearly_uniform')
        if index and index not in cuts:
            if abs(row['mean_luminance'] - rows[index-1]['mean_luminance']) > 15:
                reasons.append('global_luminance_step_over_15')
            if row['changed_fraction_above_40'] > .25:
                reasons.append('over_quarter_frame_changed_by_40')
        if reasons:
            flags.append({'frame': index, 'reasons': reasons})
    return flags


def phase_spans(samples):
    spans = []
    for index, sample in enumerate(samples):
        if spans and spans[-1]['phase'] == sample['phase']:
            spans[-1]['end_frame_exclusive'] = index + 1
        else:
            spans.append({'phase': sample['phase'], 'start_frame': index,
                          'end_frame_exclusive': index + 1})
    return spans


def inspection_indices(samples, detail=False):
    """Every second, every phase's endpoints/midpoint, dense latch transitions."""
    selected = set(range(0, len(samples), 30))
    critical = {'grasp', 'release_latch', 'seat_and_latch', 'release_gripper',
                'recover_latch_reset', 'recover_insert_release', 'seat_nudge'}
    for span in phase_spans(samples):
        start, end = span['start_frame'], span['end_frame_exclusive']
        selected.update((start, (start + end - 1) // 2, end - 1))
        if detail and span['phase'] in critical:
            selected.update(range(start, end, 3))
    return sorted(selected)


def validate_timestamps(timestamps, expected_count, fps=30):
    if len(timestamps) != expected_count or expected_count < 1:
        raise ValueError('Missing encoded frame timestamps')
    errors = [abs(t - index / fps) for index, t in enumerate(timestamps)]
    if any(not math.isfinite(t) for t in timestamps) or max(errors) > 1e-6:
        raise ValueError('Encoded presentation timestamps are not contiguous at the declared rate')
    return {'frames': expected_count, 'fps': fps, 'maximum_timestamp_error_s': max(errors),
            'first_timestamp_s': timestamps[0], 'last_timestamp_s': timestamps[-1]}
