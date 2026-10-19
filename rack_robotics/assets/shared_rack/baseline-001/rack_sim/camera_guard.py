"""Keep the demo in its perspective camera without resetting orbit or zoom."""
PERSPECTIVE='/OmniverseKit_Persp'

def protect_perspective(viewport,enabled=True):
    if viewport is None or not enabled:
        return None
    previous=str(viewport.camera_path)
    if previous==PERSPECTIVE:
        return None
    viewport.camera_path=PERSPECTIVE
    return previous
