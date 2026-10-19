"""Controller guards independent of Isaac Sim; contact tests run on the VM."""
import unittest
from types import SimpleNamespace
from rack_sim.row_demo import RowDemo

class FakeInteraction:
    def __init__(self):
        self.connected_port=None; self.port_index=0; self.target=[0,.05,0]
        self.ports=[('port'+str(i),(i*.025,0,0)) for i in range(16)]
        self.metrics={'depth_m':0}; self.position=(0,.05,0); self.clip=False
    def set_grasp(self,value): pass
    def release(self,value): self.clip=value
    def port_target(self,index,clearance=.05): return [index*.025,clearance,0]
    def set_target(self,target): self.target=target
    def pose(self): return self.position,None

class RowDemoTests(unittest.TestCase):
    def test_extract_does_not_traverse_before_clearance(self):
        interaction=FakeInteraction(); demo=RowDemo(interaction)
        demo.start(False,1); demo.tick(1.3)
        self.assertEqual(demo.phase,'extract')
        interaction.metrics['depth_m']=-.05; demo.tick(.01)
        self.assertEqual(demo.phase,'traverse')
        self.assertTrue(interaction.clip)

    def test_commanded_insertion_does_not_mean_connected(self):
        interaction=FakeInteraction(); demo=RowDemo(interaction)
        demo.start(False,1)
        demo.enter('insert',interaction.port_target(1,.0002),1)
        demo.tick(1.2)
        self.assertEqual(demo.phase,'insert')
        demo.tick(3.1)
        self.assertFalse(demo.running)
        self.assertIn('Timed out',demo.error)

    def test_wrong_port_is_not_success(self):
        interaction=FakeInteraction(); interaction.connected_port=0
        demo=RowDemo(interaction); demo.start(False,1)
        demo.enter('insert',interaction.port_target(1,.0002),1); demo.tick(1.2)
        self.assertEqual(demo.phase,'insert')

    def test_row_end_reverses(self):
        demo=RowDemo(FakeInteraction())
        self.assertEqual(demo.next_port(15),14)
        self.assertEqual(demo.next_port(14),13)
        self.assertEqual(demo.next_port(0),1)

    def test_press_waits_for_physical_hook_clearance(self):
        interaction=FakeInteraction(); interaction.connected_port=0
        demo=RowDemo(interaction); demo.start(False,1)
        demo.tick(.6)
        self.assertEqual(demo.phase,'press')
        demo.tick(.5)
        self.assertEqual(demo.phase,'press')
        interaction.connected_port=None
        demo.tick(.1)
        self.assertEqual(demo.phase,'press')
        interaction.metrics['hook_clear']=True
        demo.tick(.1)
        self.assertEqual(demo.phase,'extract')

if __name__=='__main__': unittest.main()
