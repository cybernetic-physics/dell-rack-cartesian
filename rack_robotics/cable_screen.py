"""Measured cable geometry, deliberately separate from tensile-force claims."""
import math

from .mechanical_screen import transform_point


def screen_cable(geometry, header, samples):
    paths = header['body_paths']
    links = geometry['links']
    if not samples or not links or len(paths) != len(set(paths)):
        raise ValueError('Missing samples/links or duplicate body paths')
    if len({link['path'] for link in links}) != len(links):
        raise ValueError('Duplicate cable link')
    indices = [paths.index(link['path']) for link in links]
    root_index = paths.index(geometry['attachment_body'])
    lengths = [math.dist(link['proximal'], link['distal']) for link in links]
    if any(not math.isfinite(length) or length <= 0 for length in lengths):
        raise ValueError('Invalid cable link length')
    total_length = sum(lengths)
    first = samples[0]['poses']
    initial_tip = transform_point(first[indices[-1]], links[-1]['distal'])
    maxima = {}
    phase_counts = {}
    previous_time = None

    def keep(name, value, row, **detail):
        if not math.isfinite(value):
            raise ValueError('Nonfinite cable observation')
        if name not in maxima or value > maxima[name]['value']:
            maxima[name] = {'value': value, 'time_s': row['time'],
                            'phase': row['phase'], **detail}

    for row in samples:
        if (len(row['poses']) != len(paths) or not math.isfinite(row['time'])
                or previous_time is not None and row['time'] <= previous_time):
            raise ValueError('Invalid pose count or sample time')
        previous_time = row['time']
        phase_counts[row['phase']] = phase_counts.get(row['phase'], 0) + 1
        anchor = transform_point(row['poses'][root_index], geometry['attachment_local'])
        previous_end = anchor
        previous_direction = None
        for i, (link, index) in enumerate(zip(links, indices)):
            pose = row['poses'][index]
            start = transform_point(pose, link['proximal'])
            end = transform_point(pose, link['distal'])
            keep('joint_anchor_gap_m', math.dist(start, previous_end), row, joint=i)
            keep('segment_centre_displacement_m', math.dist(pose[:3], first[index][:3]),
                 row, link=link['path'])
            direction = [(b-a)/lengths[i] for a, b in zip(start, end)]
            if previous_direction is not None:
                dot = max(-1., min(1., sum(a*b for a, b in zip(direction, previous_direction))))
                keep('adjacent_segment_bend_deg', math.degrees(math.acos(dot)), row, joint=i)
            previous_direction = direction
            previous_end = end
        keep('free_end_displacement_m', math.dist(previous_end, initial_tip), row)
        keep('endpoint_chord_fraction', math.dist(previous_end, anchor)/total_length, row)

    return {'samples': len(samples), 'sample_rate_hz': header.get('fps'),
            'phase_sample_counts': phase_counts, 'links': len(links),
            'nominal_chain_length_m': total_length, 'maxima': maxima,
            'sampled_attachment_gap_below_1_5mm': maxima['joint_anchor_gap_m']['value'] < .0015,
            'tensile_force_n': None, 'excessive_tension_assessment': 'unmeasured',
            'scope': 'Recorded geometry only. Chord fraction is not tension or available routing slack; '
                     'joint gap is solver error, not elastic strain. Bend is between rigid segments, '
                     'not jacket curvature. Free-ended cable does not test a taut connected far end. '
                     'Sampling can miss transient peaks; no force or material safety claim.'}
