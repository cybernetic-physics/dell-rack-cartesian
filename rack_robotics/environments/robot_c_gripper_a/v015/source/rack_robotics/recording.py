"""Record measured rigid-body transforms for later multi-camera RTX replay.

This only reads the live simulation. Playback must run with physics stopped and
must be labeled replay; recorded poses are never used to drive a physics trial.
"""
import json
from pxr import UsdGeom, UsdPhysics


class TrajectoryRecorder:
    def __init__(self,stage,path):
        self.stage=stage
        self.paths=[str(p.GetPath()) for p in stage.Traverse()
                    if p.HasAPI(UsdPhysics.RigidBodyAPI)]
        self.stream=path.open('w')
        self.stream.write(json.dumps({'format':'measured_world_poses_v1',
                                     'body_paths':self.paths,'fps':30})+'\n')
        self.stream.flush()
        self.count=0

    def sample(self,time,phase):
        cache=UsdGeom.XformCache()
        poses=[]
        for path in self.paths:
            matrix=cache.GetLocalToWorldTransform(self.stage.GetPrimAtPath(path))
            q=matrix.ExtractRotationQuat()
            poses.append([*matrix.ExtractTranslation(),q.GetReal(),*q.GetImaginary()])
        self.stream.write(json.dumps({'time':time,'phase':phase,'poses':poses})+'\n')
        self.count+=1
        if self.count==1 or self.count%30==0: self.stream.flush()

    def close(self):
        self.stream.close()
