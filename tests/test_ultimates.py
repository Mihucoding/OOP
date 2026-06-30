import unittest
from logic.abilities.ultimate.fire_nova       import FireNova
from logic.abilities.ultimate.ice_blizzard    import IceBlizzard
from logic.abilities.ultimate.lightning_storm import LightningStorm
from logic.abilities.ultimate.wind_cyclone    import WindCyclone
from logic.abilities.ultimate.shadow_nova     import ShadowNova
from logic.entities.enemy  import Enemy
from logic.entities.player import Player


class TestUltimates(unittest.TestCase):
    def setUp(self):
        self.player  = Player(0, 0)
        self.enemies = [Enemy(100, 0), Enemy(-80, 50), Enemy(0, 150)]

    def _activate(self, ult_cls):
        ult  = ult_cls()
        info = ult.activate(self.player, self.enemies, None, {})
        self.assertIn('name', info)
        self.assertIn('radius', info)
        return info

    def test_fire_nova(self):    self._activate(FireNova)
    def test_ice_blizzard(self): self._activate(IceBlizzard)
    def test_lightning(self):    self._activate(LightningStorm)
    def test_wind_cyclone(self): self._activate(WindCyclone)
    def test_shadow_nova(self):  self._activate(ShadowNova)

    def test_wind_no_crash_enemy_at_same_pos(self):
        # dist == 0 edge case
        self.enemies[0].x = 0.0
        self.enemies[0].y = 0.0
        self._activate(WindCyclone)

    def test_ice_applies_stun(self):
        IceBlizzard().activate(self.player, self.enemies, None, {})
        statuses = [e.type for e in self.enemies[0].status_effects]
        self.assertIn('stun', statuses)

    def test_wind_applies_slow(self):
        WindCyclone().activate(self.player, self.enemies, None, {})
        statuses = [e.type for e in self.enemies[0].status_effects]
        self.assertIn('slow', statuses)


if __name__ == '__main__':
    unittest.main()
