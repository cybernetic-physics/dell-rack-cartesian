"""SI units throughout. Measured hardware dimensions vs tunable approximations."""
from dataclasses import dataclass

@dataclass(frozen=True)
class ConnectorConfig:
    width: float = .01168
    height: float = .0085
    length: float = .022
    socket_width: float = .0122
    socket_height: float = .0091
    socket_depth: float = .012
    seat_depth: float = .0105
    lateral_tolerance: float = .00022
    angular_tolerance_deg: float = 2.0
    seat_dwell: float = .10
    mass: float = .008
    contact_offset: float = .00005
    physics_dt: float = 1/240
    drive_stiffness: float = 4000.0
    drive_damping: float = 10.0
    drive_max_force: float = 5.0
    cable_radius: float = .0026
    cable_segment_length: float = .015
    cable_segments: int = 36

CFG = ConnectorConfig()
# Four 6U XE9680s in a 42U, 600 x 1200 mm rack. Rear I/O wall recessed
# 110.5 mm relative to the GPU fan cage, as in Dell's dimension drawing.
SERVER_Z = (.32, .63, .94, 1.25)
SERVER_HEIGHT = .2632
REAR_IO_Y = .3555
PORT = (.066, REAR_IO_Y + .003, SERVER_Z[2] + .181)
# A genuine management Ethernet row; the neighbouring QSFP switch stays unchanged.
ROW_PORTS = tuple(((7.5-i)*.025, .429, 1.66) for i in range(16))
