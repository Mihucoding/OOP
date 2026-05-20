import unittest

from logic.entities.bullet import Bullet
from logic.entities.enemy import Enemy
from logic.entities.player import Player
from logic.rune.elements.fire_rune import FireRune
from logic.rune.elements.ice_rune import IceRune
from logic.rune.modifiers.bounce_modifier import BounceModifier
from logic.rune.modifiers.spiral_modifier import SpiralModifier
from logic.rune.rune_slots import RuneSlots


class TestRuneSlotRules(unittest.TestCase):
    """Kiểm tra quy tắc slot sau khi đổi sang Hướng B (nhánh chỉ nhận Modifier)."""

    def test_slot0_accepts_element_rune(self):
        # Slot 0 (hệ chính) nhận ElementRune
        slots = RuneSlots()
        self.assertTrue(slots.place(0, FireRune()))

    def test_slot0_rejects_modifier_rune(self):
        # Slot 0 không nhận ModifierRune
        slots = RuneSlots()
        self.assertFalse(slots.place(0, SpiralModifier()))
        self.assertFalse(slots.place(0, BounceModifier()))

    def test_branch_slots_reject_element_rune(self):
        # Slot 1/2/3/4 (nhánh) chỉ nhận Modifier, không nhận Element
        slots = RuneSlots()
        self.assertFalse(slots.place(1, FireRune()))
        self.assertFalse(slots.place(2, FireRune()))

    def test_modifier_can_be_placed_without_element(self):
        # Slot 1/2 đặt được ngay khi Slot 0 trống
        slots = RuneSlots()
        self.assertTrue(slots.place(1, SpiralModifier()))
        self.assertTrue(slots.place(2, BounceModifier()))

    def test_child_slot_requires_parent(self):
        # Slot 3 cần Slot 1; Slot 4 cần Slot 2
        slots = RuneSlots()
        self.assertFalse(slots.place(3, SpiralModifier()))
        self.assertFalse(slots.place(4, BounceModifier()))

        slots.place(1, SpiralModifier())
        self.assertTrue(slots.place(3, BounceModifier()))

    def test_slot0_optional_tree_still_fires(self):
        # Khi Slot 0 trống, cây vẫn có thể bắn (is_ready = True)
        slots = RuneSlots()
        slots.place(1, SpiralModifier())
        tree = slots.build_rune_tree()
        self.assertTrue(tree.is_ready())
        self.assertEqual(len(tree.elements), 0)
        self.assertEqual(len(tree.modifiers), 1)


class TestRuneTreeBehavior(unittest.TestCase):
    """Kiểm tra hành vi RuneTree từ RuneSlots."""

    def test_spiral_only_tree_changes_bullet_direction(self):
        slots = RuneSlots()
        slots.place(1, SpiralModifier())
        tree = slots.build_rune_tree()
        bullet = Bullet(0, 0, 100, 0, 20, tree)
        old_vx, old_vy = bullet.vx, bullet.vy

        bullet.update(0.5)

        self.assertNotEqual(bullet.vx, old_vx)
        self.assertNotEqual(bullet.vy, old_vy)

    def test_bounce_only_tree_redirects_bullet(self):
        slots = RuneSlots()
        slots.place(2, BounceModifier())
        tree = slots.build_rune_tree()
        enemy_a = Enemy(100, 0)
        enemy_b = Enemy(200, 0)
        bullet = Bullet(0, 0, 100, 0, 20, tree)
        bullet.x = enemy_a.x
        bullet.y = enemy_a.y

        bullet.on_hit(enemy_a, {'enemies': [enemy_a, enemy_b], 'bullets': []})

        self.assertTrue(bullet.alive)
        self.assertEqual(bullet.bounce_count, 1)
        self.assertGreater(bullet.vx, 0)

    def test_element_in_slot0_applies_burn(self):
        # Fire ở Slot 0 → gây burn khi trúng
        slots = RuneSlots()
        slots.place(0, FireRune())
        tree = slots.build_rune_tree()
        enemy = Enemy(100, 0)
        bullet = Bullet(0, 0, 100, 0, 20, tree)

        bullet.on_hit(enemy, {'enemies': [enemy], 'bullets': []})

        self.assertEqual(len(enemy.status_effects), 1)
        self.assertEqual(enemy.status_effects[0].type, 'burn')

    def test_combo_tree_element_slot0_and_modifiers(self):
        # Fire ở Slot 0 + Spiral Slot 1 + Bounce Slot 2
        slots = RuneSlots()
        slots.place(0, FireRune())
        slots.place(1, SpiralModifier())
        slots.place(2, BounceModifier())
        tree = slots.build_rune_tree()

        self.assertEqual(len(tree.elements), 1)
        self.assertEqual(len(tree.modifiers), 2)

    def test_build_order_slot0_then_left_then_right(self):
        # Thứ tự trong tree: element trước, nhánh trái (Slot 1) trước phải (Slot 2)
        slots = RuneSlots()
        fire    = FireRune()
        spiral  = SpiralModifier()
        bounce  = BounceModifier()
        slots.place(0, fire)
        slots.place(1, spiral)
        slots.place(2, bounce)
        tree = slots.build_rune_tree()

        runes = tree.get_all_runes()
        # Element phải có mặt
        self.assertIn(fire, runes)
        # Spiral (L1, index thấp hơn) trước Bounce (R1) trong danh sách modifiers
        mod_names = [type(m).__name__ for m in tree.modifiers]
        self.assertLess(mod_names.index("SpiralModifier"), mod_names.index("BounceModifier"))


class TestPlayerSpells(unittest.TestCase):
    """Kiểm tra 3 chiêu độc lập của Player."""

    def test_player_has_three_independent_spells(self):
        player = Player()
        self.assertEqual(len(player.spells), 3)

        player.spells[0].rune_slots.place(1, SpiralModifier())
        player.spells[1].rune_slots.place(1, BounceModifier())
        player.rebuild_all_spells()

        self.assertEqual(len(player.spells[0].rune_tree.modifiers), 1)
        self.assertEqual(len(player.spells[1].rune_tree.modifiers), 1)
        self.assertEqual(len(player.spells[2].rune_tree.modifiers), 0)

        player.set_active_spell(1)
        self.assertIs(player.rune_tree, player.spells[1].rune_tree)


class TestSameElementStacking(unittest.TestCase):
    """Kiểm tra cơ chế stack cùng hệ: same-element rune vào modifier slot."""

    def test_same_element_allowed_in_modifier_slot(self):
        # Slot 0: Fire → Slot 1: Fire cùng hệ → được phép
        slots = RuneSlots()
        slots.place(0, FireRune())
        self.assertTrue(slots.place(1, FireRune()))

    def test_different_element_blocked_in_modifier_slot(self):
        # Slot 0: Fire → Slot 1: Ice khác hệ → bị block
        slots = RuneSlots()
        slots.place(0, FireRune())
        self.assertFalse(slots.place(1, IceRune()))

    def test_element_blocked_in_modifier_slot_when_slot0_empty(self):
        # Slot 0 trống → modifier slot không nhận bất kỳ Element nào
        slots = RuneSlots()
        self.assertFalse(slots.place(1, FireRune()))
        self.assertFalse(slots.place(2, IceRune()))

    def test_stack_count_in_tree(self):
        # Slot 0: Fire (stack=1) + Slot 1: Fire → element_stack = 2
        slots = RuneSlots()
        fire0 = FireRune()
        slots.place(0, fire0)
        slots.place(1, FireRune())
        tree = slots.build_rune_tree()

        self.assertEqual(len(tree.elements), 1)   # chỉ 1 element trong tree
        self.assertEqual(fire0.element_stack, 2)   # nhưng stack = 2

    def test_stack_count_three(self):
        # Slot 0 + Slot 1 + Slot 2 cùng Fire → stack = 3
        slots = RuneSlots()
        fire0 = FireRune()
        slots.place(0, fire0)
        slots.place(1, FireRune())
        slots.place(2, FireRune())
        tree = slots.build_rune_tree()

        self.assertEqual(len(tree.elements), 1)
        self.assertEqual(fire0.element_stack, 3)

    def test_stack_boost_increases_damage(self):
        # Fire x2 → burn damage nhân đôi khi trúng
        slots = RuneSlots()
        slots.place(0, FireRune())
        slots.place(1, FireRune())
        tree = slots.build_rune_tree()

        enemy = Enemy(100, 0)
        bullet = Bullet(0, 0, 100, 0, 20, tree)
        bullet.on_hit(enemy, {'enemies': [enemy], 'bullets': []})

        self.assertEqual(len(enemy.status_effects), 1)
        effect = enemy.status_effects[0]
        self.assertEqual(effect.type, 'burn')
        # damage_per_sec = BURN_DAMAGE * stack = 8.0 * 2 = 16.0
        self.assertAlmostEqual(effect.damage_per_sec, 16.0)

    def test_modifier_and_same_element_coexist(self):
        # Slot 0: Fire, Slot 1: Spiral (Modifier), Slot 2: Fire (stack) → hợp lệ
        slots = RuneSlots()
        slots.place(0, FireRune())
        self.assertTrue(slots.place(1, SpiralModifier()))
        self.assertTrue(slots.place(2, FireRune()))
        tree = slots.build_rune_tree()

        self.assertEqual(len(tree.elements), 1)
        self.assertEqual(len(tree.modifiers), 1)
        self.assertEqual(tree.elements[0].element_stack, 2)

    def test_same_element_child_slot_needs_parent(self):
        # Slot 0: Fire → Slot 3: Fire cần Slot 1 có rune trước
        slots = RuneSlots()
        slots.place(0, FireRune())
        self.assertFalse(slots.place(3, FireRune()))  # Slot 1 trống → không được

        slots.place(1, SpiralModifier())
        self.assertTrue(slots.place(3, FireRune()))   # Slot 1 có rune → được


if __name__ == '__main__':
    unittest.main()
