"""SI-unit inverse position maps; these produce joint commands, never poses."""


def joint_coordinates(architecture,tcp,tool_offset=.13):
    if architecture not in ('A','B'): raise ValueError(architecture)
    x,y,z=map(float,tcp)
    q={'x':x,'y':y+tool_offset-.68,'z':z-1.80}
    travel=.20 if architecture=='B' else .21
    if not (-travel<=x<=travel and -.125<=q['y']<=.000001 and -.70<=q['z']<=.000001):
        raise ValueError(f'TCP outside {architecture} joint limits: {tcp}')
    if architecture=='B':
        del q['x']
        q.update(x_outer=(x+.20)/2,x_inner=(x+.20)/2)
    return q
