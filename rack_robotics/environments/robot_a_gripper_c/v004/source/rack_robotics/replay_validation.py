"""Pure numerical checks for recorded-motion visualization, never task control."""
import math


def validate_capture_camera(actual, expected, tolerance=1e-4):
    """Compare renderer-reported and USD world-to-camera matrices."""
    values = [float(matrix[i][j]) for matrix in (actual, expected)
              for i in range(4) for j in range(4)]
    if not all(math.isfinite(value) for value in values):
        raise ValueError('Non-finite capture camera matrix')
    error = max(abs(a-b) for a, b in zip(values[:16], values[16:]))
    if error > tolerance:
        raise ValueError(f'Captured camera does not match replay camera: {error}')
    return error


def rotation_error_rad(first, second):
    if len(first) != 4 or len(second) != 4:
        raise ValueError('Expected wxyz quaternions')
    lengths = [math.sqrt(sum(v*v for v in q)) for q in (first, second)]
    if any(not math.isfinite(v) or v < 1e-12 for v in lengths):
        raise ValueError('Invalid quaternion')
    a = [v/lengths[0] for v in first]; b = [v/lengths[1] for v in second]
    # q and -q are equivalent; atan2 avoids acos cancellation near zero.
    sign = 1 if sum(x*y for x, y in zip(a, b)) >= 0 else -1
    chord = math.sqrt(sum((x-sign*y)**2 for x, y in zip(a, b)))
    return 4*math.asin(min(1., chord/2))


def validate_recording(header, samples):
    if header.get('format') != 'measured_world_poses_v1' or header.get('fps') != 30:
        raise ValueError('Expected measured 30 Hz world poses')
    paths = header['body_paths']
    if len(paths) != len(set(paths)) or '/World/Plug' not in paths or '/World/Latch' not in paths:
        raise ValueError('Missing or duplicate recorded bodies')
    if not samples:
        raise ValueError('Empty recording')
    previous = None
    for index, sample in enumerate(samples):
        timestamp = sample['time']
        if not math.isfinite(timestamp) or (previous is not None and timestamp <= previous):
            raise ValueError('Non-increasing or invalid recorded time')
        if abs(timestamp-samples[0]['time']-index/30) > .01:
            raise ValueError('Recording cadence cannot be replayed at 30 fps without retiming')
        previous = timestamp
        if len(sample['poses']) != len(paths):
            raise ValueError('Pose/body count mismatch')
        for pose in sample['poses']:
            if len(pose) != 7 or not all(math.isfinite(v) for v in pose):
                raise ValueError('Invalid recorded pose')
            if abs(sum(v*v for v in pose[3:])-1) > 1e-4:
                raise ValueError('Non-unit recorded rotation')
    return {'samples': len(samples), 'body_count': len(paths),
            'start_s': samples[0]['time'], 'end_s': samples[-1]['time'],
            'max_timing_residual_s': max(abs(s['time']-samples[0]['time']-i/30) for i, s in enumerate(samples))}
