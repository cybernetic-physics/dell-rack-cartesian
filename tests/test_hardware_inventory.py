import copy
import unittest
from rack_robotics.hardware_inventory import component, inventory


class HardwareInventoryTest(unittest.TestCase):
    def props(self):
        body='/World/Robot/Bridge'
        shapes=[{'path':body+'/GuideInterfaces/LiftBlock0/'+name,
                 'lower_m':[0,0,0],'upper_m':[.027,.013,.0454]}
                for name in ('Crown','Side0','Side1')]
        return {'passed':True,'robot':'A','gripper':'A','bodies':{body:{'geometry':shapes}}}

    def test_composite_block_is_one_component_and_cost_unknown(self):
        result=inventory(self.props())
        self.assertEqual(result['geometry_records'],3)
        self.assertEqual(result['component_counts'],{'guide_blocks':1})
        self.assertIsNone(result['complete_purchase_cost_usd'])
        self.assertEqual(len(result['components'][0]['geometry_paths']),3)

    def test_accessories_not_counted_as_motors_rails_or_blocks(self):
        for path in ('Frame/MotorPlate/U0','Frame/GuideInterfaces/RailShim0',
                     'Carriage/DepthFrontBearingPost0','Carriage/ScrewInterfaces/TraverseMotorShaft'):
            self.assertEqual(component('/World/Robot/'+path)[0],'other_geometry')
        self.assertEqual(component('/World/Robot/Carriage/DepthMotor')[0],'axis_motor_envelopes')
        self.assertEqual(component('/World/Robot/ServiceCarriers/Lift/Link000/Side0'),
                         ('carrier_links','/World/Robot/ServiceCarriers/Lift/Link000'))

    def test_invalid_bounds_duplicate_and_failed_query_rejected(self):
        p=self.props(); p['passed']=False
        with self.assertRaises(ValueError):inventory(p)
        p=self.props(); shapes=next(iter(p['bodies'].values()))['geometry']; shapes.append(copy.deepcopy(shapes[0]))
        with self.assertRaises(ValueError):inventory(p)
        p=self.props(); next(iter(p['bodies'].values()))['geometry'][0]['lower_m'][0]=float('nan')
        with self.assertRaises(ValueError):inventory(p)


if __name__=='__main__':unittest.main()
