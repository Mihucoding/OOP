import itertools
import math
import random
import unittest

from logic.entities.bullet import Bullet
from logic.entities.enemy import Enemy
from logic.entities.player import Player
from logic.rune.elements.fire_rune import FireRune
from logic.rune.elements.ice_rune import IceRune
from logic.rune.modifiers.hit_and_run_modifier import HitAndRunModifier
from logic.rune.modifiers.twist_of_fate_modifier import TwistOfFateModifier
from logic.rune.modifiers.stars_aligned_modifier import StarsAlignedModifier
from logic.rune.modifiers.haste_rune import HasteRune
from logic.rune.rune_slots import RuneSlots
from logic.rune.rune_tree import RuneTree


class TestRuneSlotRules(unittest.TestCase):
    """Kiểm tra quy tắc slot sau khi đổi sang Hướng B (nhánh chỉ nhận Modifier)."""

    def test_slot0_accepts_element_rune(self):
        # Slot 0 (hệ chính) nhận ElementRune
        slots = RuneSlots()
        self.assertTrue(slots.place(0, FireRune()))

    def test_slot0_rejects_modifier_rune(self):
        # Slot 0 không nhận ModifierRune
        slots = RuneSlots()
        self.assertFalse(slots.place(0, TwistOfFateModifier()))
        self.assertFalse(slots.place(0, HitAndRunModifier()))

    def test_branch_slots_reject_element_rune(self):
        # Slot 1/2/3/4 (nhánh) chỉ nhận Modifier, không nhận Element
        slots = RuneSlots()
        self.assertFalse(slots.place(1, FireRune()))
        self.assertFalse(slots.place(2, FireRune()))

    def test_modifier_can_be_placed_without_element(self):
        # Slot 1/2 đặt được ngay khi Slot 0 trống
        slots = RuneSlots()
        self.assertTrue(slots.place(1, TwistOfFateModifier()))
        self.assertTrue(slots.place(2, HitAndRunModifier()))

    def test_child_slot_no_longer_requires_parent(self):
        # Mới: node con đặt được ngay cả khi node cha trống (tự nối lên root)
        slots = RuneSlots()
        self.assertTrue(slots.place(3, TwistOfFateModifier()))
        self.assertTrue(slots.place(4, HitAndRunModifier()))

    def test_slot0_optional_tree_still_fires(self):
        # Khi Slot 0 trống, cây vẫn có thể bắn (is_ready = True)
        slots = RuneSlots()
        slots.place(1, TwistOfFateModifier())
        tree = slots.build_rune_tree()
        self.assertTrue(tree.is_ready())
        self.assertEqual(len(tree.elements), 0)
        self.assertEqual(len(tree.modifiers), 1)


class TestRuneTreeBehavior(unittest.TestCase):
    """Kiểm tra hành vi RuneTree từ RuneSlots."""

    def test_spiral_only_tree_changes_bullet_direction(self):
        slots = RuneSlots()
        slots.place(1, TwistOfFateModifier())
        tree = slots.build_rune_tree()
        bullet = Bullet(0, 0, 100, 0, 20, tree)
        old_vx, old_vy = bullet.vx, bullet.vy

        bullet.update(0.5)

        self.assertNotEqual(bullet.vx, old_vx)
        self.assertNotEqual(bullet.vy, old_vy)

    def test_bounce_only_tree_does_not_redirect_on_enemy_hit(self):
        # Hit-And-Run giờ là phản xạ TƯỜNG (game_loop xử lý), không còn nảy
        # sang địch gần nhất trong on_hit() nữa — trúng địch thì chết như đạn
        # thường (không có pierce/bounce nào can thiệp ở đây).
        slots = RuneSlots()
        slots.place(2, HitAndRunModifier())
        tree = slots.build_rune_tree()
        enemy_a = Enemy(100, 0)
        enemy_b = Enemy(200, 0)
        bullet = Bullet(0, 0, 100, 0, 20, tree)
        bullet.x = enemy_a.x
        bullet.y = enemy_a.y

        bullet.on_hit(enemy_a, {'enemies': [enemy_a, enemy_b], 'bullets': []})

        self.assertFalse(bullet.alive)
        self.assertEqual(bullet.bounce_count, 0)

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
        slots.place(1, TwistOfFateModifier())
        slots.place(2, HitAndRunModifier())
        tree = slots.build_rune_tree()

        self.assertEqual(len(tree.elements), 1)
        self.assertEqual(len(tree.modifiers), 2)

    def test_build_order_slot0_then_left_then_right(self):
        # Thứ tự trong tree: element trước, nhánh trái (Slot 1) trước phải (Slot 2)
        slots = RuneSlots()
        fire    = FireRune()
        spiral  = TwistOfFateModifier()
        bounce  = HitAndRunModifier()
        slots.place(0, fire)
        slots.place(1, spiral)
        slots.place(2, bounce)
        tree = slots.build_rune_tree()

        runes = tree.get_all_runes()
        # Element phải có mặt
        self.assertIn(fire, runes)
        # Spiral (L1, index thấp hơn) trước Bounce (R1) trong danh sách modifiers
        mod_names = [type(m).__name__ for m in tree.modifiers]
        self.assertLess(mod_names.index("TwistOfFateModifier"), mod_names.index("HitAndRunModifier"))


class TestPlayerSpells(unittest.TestCase):
    """Kiểm tra 2 chiêu độc lập của Player (mô hình chọn 2 hệ)."""

    def test_player_has_two_independent_spells(self):
        player = Player()
        self.assertEqual(len(player.spells), 2)

        player.spells[0].rune_slots.place(1, TwistOfFateModifier())
        player.spells[1].rune_slots.place(1, HitAndRunModifier())
        player.rebuild_all_spells()

        self.assertEqual(len(player.spells[0].rune_tree.modifiers), 1)
        self.assertEqual(len(player.spells[1].rune_tree.modifiers), 1)

        player.set_active_spell(1)
        self.assertIs(player.rune_tree, player.spells[1].rune_tree)

    def test_setup_spells_assigns_locked_core(self):
        player = Player()
        player.setup_spells([FireRune(), IceRune()])
        self.assertEqual(len(player.spells), 2)
        for spell in player.spells:
            core = spell.rune_slots.get(0)
            self.assertIsNotNone(core.rune)
            self.assertTrue(core.locked)
        # Lõi đã khóa: không đổi/không gỡ được
        fire_spell = player.spells[0]
        self.assertFalse(fire_spell.rune_slots.can_place(0, IceRune()))
        self.assertIsNone(fire_spell.rune_slots.remove(0))
        self.assertIsNone(fire_spell.rune_slots.swap(0, IceRune()))
        self.assertIsNotNone(fire_spell.rune_slots.get(0).rune)


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
        self.assertTrue(slots.place(1, TwistOfFateModifier()))
        self.assertTrue(slots.place(2, FireRune()))
        tree = slots.build_rune_tree()

        self.assertEqual(len(tree.elements), 1)
        self.assertEqual(len(tree.modifiers), 1)
        self.assertEqual(tree.elements[0].element_stack, 2)

    def test_same_element_child_slot_auto_connects(self):
        # Mới: Slot 0 Fire → Slot 3 Fire đặt được ngay dù Slot 1 trống (tự nối lên)
        slots = RuneSlots()
        slots.place(0, FireRune())
        self.assertTrue(slots.place(3, FireRune()))
        # Vẫn phải cùng hệ mới stack
        slots2 = RuneSlots()
        slots2.place(0, FireRune())
        self.assertFalse(slots2.place(3, IceRune()))


class TestModifierCompatibility(unittest.TestCase):
    """Hit-And-Run (phản xạ tường) hợp với cả 4 hệ — không còn bị cấm trên
    beam (Lightning), spike (Ice), boomerang (Wind) như bản redirect-tới-địch
    cũ nữa."""

    def _core(self, elem_cls):
        from logic.rune.rune_slots import slot_defs_for_rune
        e = elem_cls()
        s = RuneSlots(slot_defs_for_rune(e))
        s.set_core(e)
        return s

    def test_fire_accepts_bounce(self):
        s = self._core(FireRune)
        self.assertTrue(s.place(1, HitAndRunModifier()))

    def test_lightning_accepts_bounce(self):
        from logic.rune.elements.lightning_rune import LightningRune
        s = self._core(LightningRune)
        self.assertTrue(s.place(1, HitAndRunModifier()))
        self.assertTrue(s.place(2, TwistOfFateModifier()))

    def test_ice_accepts_bounce(self):
        s = self._core(IceRune)
        self.assertTrue(s.place(1, HitAndRunModifier()))

    def test_wind_accepts_bounce(self):
        from logic.rune.elements.wind_rune import WindRune
        s = self._core(WindRune)
        self.assertTrue(s.place(1, HitAndRunModifier()))
        self.assertTrue(s.place(2, TwistOfFateModifier()))


class TestAutoConnectBranch(unittest.TestCase):
    """Modifier ở node rời (cha trống) tự nối lên tổ tiên gần nhất — không bị bỏ."""

    def _wind_slots(self):
        from logic.rune.rune_slots import slot_defs_for_rune
        from logic.rune.elements.wind_rune import WindRune
        e = WindRune()
        s = RuneSlots(slot_defs_for_rune(e))
        s.set_core(e)
        return s

    def test_can_place_child_without_parent(self):
        s = self._wind_slots()
        child = next(sl for sl in s.slots
                     if sl.slot_type == 'modifier' and sl.parent_id not in (None, 0))
        self.assertTrue(s.place(child.id, TwistOfFateModifier()))

    def test_orphan_modifier_enters_tree(self):
        s = self._wind_slots()
        child = next(sl for sl in s.slots
                     if sl.slot_type == 'modifier' and sl.parent_id not in (None, 0))
        s.place(child.id, TwistOfFateModifier())
        tree = s.build_rune_tree()
        self.assertEqual(len(tree.modifiers), 1)  # nối thẳng root, không bị bỏ

    def test_effective_parent_skips_empty(self):
        s = self._wind_slots()
        child = next(sl for sl in s.slots
                     if sl.slot_type == 'modifier' and sl.parent_id not in (None, 0))
        s.place(child.id, TwistOfFateModifier())
        # cha trực tiếp trống → tổ tiên hiệu dụng là 0 (lõi) hoặc node có rune gần nhất
        self.assertEqual(s.effective_parent(child.id), 0)


class TestWindBoomerangModifiers(unittest.TestCase):
    """Wind là đạn bay → Spiral làm cong quỹ đạo lúc ra."""

    def test_spiral_curves_boomerang(self):
        from logic.rune.rune_slots import slot_defs_for_rune
        from logic.rune.elements.wind_rune import WindRune
        from logic.entities.wind_boomerang import WindBoomerang
        e = WindRune()
        s = RuneSlots(slot_defs_for_rune(e))
        s.set_core(e)
        s.place(1, TwistOfFateModifier())
        tree = s.build_rune_tree()

        wb = WindBoomerang(0, 0, 100, 0, 20, tree)
        v0 = (wb.vx, wb.vy)
        wb.update(0.2)
        self.assertNotEqual((round(wb.vx, 3), round(wb.vy, 3)),
                            (round(v0[0], 3), round(v0[1], 3)))


class TestModifierPointBudget(unittest.TestCase):
    """Mỗi chiêu có ngân sách RuneSlots.MAX_POINTS (=5) điểm cho modifier.
    Twist of Fate/Haste/Bounce tốn 1 điểm; Stars Aligned tốn 2 điểm."""

    def test_costs_as_expected(self):
        self.assertEqual(TwistOfFateModifier.POINT_COST, 1)
        self.assertEqual(HasteRune.POINT_COST, 1)
        self.assertEqual(HitAndRunModifier.POINT_COST, 1)
        self.assertEqual(StarsAlignedModifier.POINT_COST, 2)

    def test_used_points_accumulates(self):
        slots = RuneSlots()
        slots.place(1, TwistOfFateModifier())   # +1
        slots.place(2, StarsAlignedModifier())  # +2
        self.assertEqual(slots.used_points(), 3)

    def test_blocks_placement_over_budget(self):
        slots = RuneSlots()   # 5 slot: 0(element),1,2,3,4 (modifier)
        slots.place(1, StarsAlignedModifier())  # 2
        slots.place(2, StarsAlignedModifier())  # 2 -> tong 4
        slots.place(3, StarsAlignedModifier())  # +2 se vuot 5 -> phai bi chan
        self.assertFalse(slots.can_place(4, StarsAlignedModifier()))
        self.assertIsNone(slots.get(4).rune)

    def test_allows_placement_exactly_at_budget(self):
        slots = RuneSlots()
        slots.place(1, StarsAlignedModifier())  # 2
        slots.place(2, StarsAlignedModifier())  # 2 -> tong 4
        self.assertTrue(slots.place(3, TwistOfFateModifier()))  # +1 = 5, vua du
        self.assertEqual(slots.used_points(), 5)

    def test_removing_frees_budget(self):
        slots = RuneSlots()
        slots.place(1, StarsAlignedModifier())  # 2
        slots.place(2, StarsAlignedModifier())  # 2 -> tong 4
        self.assertFalse(slots.place(3, StarsAlignedModifier()))  # +2 vuot 5 -> bi chan, slot 3 con trong
        slots.remove(2)                     # tra lai 2 diem -> con 2 (tu slot 1)
        self.assertTrue(slots.place(3, StarsAlignedModifier()))   # gio dat duoc (2+2=4 <=5)

    def test_swap_respects_budget(self):
        slots = RuneSlots()
        slots.place(1, StarsAlignedModifier())  # 2
        slots.place(2, StarsAlignedModifier())  # 2 -> tong 4
        slots.place(3, TwistOfFateModifier())   # 1 -> tong 5 (dung khop)
        # Doi Twist of Fate (cost1) thanh Stars Aligned (cost2) se vuot ngan sach -> bi chan
        self.assertIsNone(slots.swap(3, StarsAlignedModifier()))
        # Doi Twist of Fate thanh Haste (cung cost1) van hop le
        self.assertIsNotNone(slots.swap(3, HasteRune()))


class TestLevelUpNoElements(unittest.TestCase):
    """Lên cấp chỉ sinh Modifier; toi da 2 ban moi loai roi ngung sinh loai do."""

    def test_choices_never_contain_element_rune(self):
        from logic.leveling.level_manager import LevelManager
        from logic.rune.rune_component import ElementRune
        player = Player()
        mgr = LevelManager()
        for wave in range(0, 20):
            mgr.trigger_level_up(wave, player)
            for choice in mgr.current_choices:
                self.assertNotIsInstance(choice, ElementRune)

    def test_stops_generating_type_after_two_copies(self):
        from logic.leveling.level_manager import LevelManager
        player = Player()
        player.rune_inventory = [TwistOfFateModifier(), TwistOfFateModifier()]  # da co 2 ban
        mgr = LevelManager()
        for _ in range(30):
            mgr.trigger_level_up(0, player)   # wave 0 -> co rune_count > 0
            for choice in mgr.current_choices:
                self.assertNotIsInstance(choice, TwistOfFateModifier)

    def test_falls_back_to_stats_when_all_maxed(self):
        from logic.leveling.level_manager import LevelManager, ALL_RUNES
        from logic.leveling.stat_upgrade import StatUpgrade
        player = Player()
        player.rune_inventory = [cls() for cls in ALL_RUNES for _ in range(2)]  # max ca 4 loai
        mgr = LevelManager()
        mgr.trigger_level_up(0, player)
        self.assertEqual(len(mgr.current_choices), 3)
        for choice in mgr.current_choices:
            self.assertIsInstance(choice, StatUpgrade)


class TestLightenedHeartAndPiercingEyes(unittest.TestCase):
    """2 modifier mới: Lightened Heart (speed+/size-) và Piercing Eyes (xuyên đạn)."""

    def _tree_with(self, *modifiers):
        slots = RuneSlots()
        slots.place(0, FireRune())
        for i, m in enumerate(modifiers, start=1):
            slots.place(i, m)
        return slots.build_rune_tree()

    def test_lightened_heart_boosts_speed_shrinks_radius(self):
        from logic.rune.modifiers.lightened_heart_modifier import LightenedHeartModifier
        tree = self._tree_with(LightenedHeartModifier())
        b = Bullet(0, 0, 100, 0, 20, tree)
        v0, r0 = (b.vx, b.vy), b.radius
        tree.on_fire(b, {'enemies': [], 'bullets': []})
        self.assertAlmostEqual(b.vx, v0[0] * 1.4)
        self.assertAlmostEqual(b.radius, r0 * 0.8)

    def test_piercing_eyes_survives_one_extra_hit(self):
        from logic.rune.modifiers.piercing_eyes_modifier import PiercingEyesModifier
        tree = self._tree_with(PiercingEyesModifier())
        b = Bullet(0, 0, 100, 0, 20, tree)
        tree.on_fire(b, {'enemies': [], 'bullets': []})
        self.assertEqual(b.pierce_remaining, 1)

        e1 = Enemy(0, 0)
        r = b.on_hit(e1, {'enemies': [e1], 'bullets': []})
        self.assertIsNot(r, False)
        self.assertTrue(b.alive)          # con 1 pierce -> song sau lan trung dau

        e2 = Enemy(10, 0)
        b.on_hit(e2, {'enemies': [e1, e2], 'bullets': []})
        self.assertFalse(b.alive)         # het pierce -> chet sau lan trung thu 2

    def test_piercing_eyes_does_not_double_damage_same_enemy(self):
        from logic.rune.modifiers.piercing_eyes_modifier import PiercingEyesModifier
        tree = self._tree_with(PiercingEyesModifier())
        b = Bullet(0, 0, 100, 0, 20, tree)
        tree.on_fire(b, {'enemies': [], 'bullets': []})

        e1 = Enemy(0, 0)
        hp0 = e1.hp
        applied = 0
        for _ in range(3):   # gia lap dan dinh hitbox nhieu frame lien
            if b.on_hit(e1, {'enemies': [e1], 'bullets': []}) is not False:
                e1.take_damage(b.damage)
                applied += 1
        self.assertEqual(applied, 1)
        self.assertAlmostEqual(hp0 - e1.hp, b.damage)


class TestFuriousOutburst(unittest.TestCase):
    """Rune Trigger: nổ cầu lửa theo quãng đường (Fire/Wind) hoặc 1 lần/cast
    cho đòn tức thời (Lightning/Ice, xử lý ở game_loop qua trigger_once)."""

    def _tree_with_outburst(self):
        from logic.rune.modifiers.furious_outburst_modifier import FuriousOutburstModifier
        slots = RuneSlots()
        slots.place(0, FireRune())
        slots.place(1, FuriousOutburstModifier())
        return slots.build_rune_tree()

    def test_on_fire_casts_one_immediately(self):
        tree = self._tree_with_outburst()
        b = Bullet(0, 0, 100, 0, 20, tree)
        ctx = {'enemies': [], 'bullets': []}
        # Fireball lúc on_fire được trả về qua return (không tự append vào ctx)
        # để RuneTree có thể áp tiếp rune con lên nó bất kể thứ tự cha/con.
        new_bullets = tree.on_fire(b, ctx)
        self.assertEqual(len(new_bullets), 1)
        self.assertEqual(new_bullets[0].visual_type, 'fire_bolt')
        self.assertAlmostEqual(new_bullets[0].damage, 20 * 0.20)

    def test_on_update_casts_by_distance(self):
        from logic.rune.modifiers.furious_outburst_modifier import FuriousOutburstModifier
        tree = self._tree_with_outburst()
        b = Bullet(0, 0, 100, 0, 20, tree)
        ctx = {'enemies': [], 'bullets': []}
        new_bullets = tree.on_fire(b, ctx)   # 1 quả ngay lúc bắn, qua return
        self.assertEqual(len(new_bullets), 1)

        # Bullet bay 400px/s; đi 0.9s = 360px = 3 lần TRIGGER_DISTANCE(120) -> +3 qua
        # (những lần lặp qua on_update vẫn tự append thẳng vào ctx['bullets'])
        tree.on_update(b, 0.9, ctx)
        self.assertEqual(len(ctx['bullets']), 3)

    def test_no_crash_without_context(self):
        tree = self._tree_with_outburst()
        b = Bullet(0, 0, 100, 0, 20, tree)
        tree.on_update(b, 0.5, None)   # context=None (VD gọi thiếu) khong duoc crash

    def test_trigger_once_applies_burn(self):
        from logic.rune.modifiers.furious_outburst_modifier import FuriousOutburstModifier
        rune = FuriousOutburstModifier()
        ctx = {'bullets': []}
        fireball = rune.trigger_once(0, 0, 100, ctx)
        enemy = Enemy(10, 0)
        fireball.on_hit(enemy, {'enemies': [enemy], 'bullets': []})
        self.assertEqual(len(enemy.status_effects), 1)
        self.assertEqual(enemy.status_effects[0].type, 'burn')

    def test_point_cost(self):
        from logic.rune.modifiers.furious_outburst_modifier import FuriousOutburstModifier
        self.assertEqual(FuriousOutburstModifier.POINT_COST, 2)


class TestHeavyHitter(unittest.TestCase):
    def test_boosts_damage_reduces_speed(self):
        from logic.rune.modifiers.heavy_hitter_modifier import HeavyHitterModifier
        slots = RuneSlots()
        slots.place(0, FireRune())
        slots.place(1, HeavyHitterModifier())
        tree = slots.build_rune_tree()
        b = Bullet(0, 0, 100, 0, 20, tree)
        v0 = b.vx
        tree.on_fire(b, {'enemies': [], 'bullets': []})
        self.assertAlmostEqual(b.damage, 20 * 1.5)
        self.assertAlmostEqual(b.vx, v0 * 0.75)


class TestRollingStone(unittest.TestCase):
    def test_on_fire_spawns_one_boulder_with_custom_duration(self):
        from logic.rune.modifiers.rolling_stone_modifier import RollingStoneModifier
        slots = RuneSlots()
        slots.place(0, FireRune())
        slots.place(1, RollingStoneModifier())
        tree = slots.build_rune_tree()
        b = Bullet(0, 0, 100, 0, 20, tree)
        ctx = {'enemies': [], 'bullets': []}
        new_bullets = tree.on_fire(b, ctx)
        self.assertEqual(len(new_bullets), 1)
        boulder = new_bullets[0]
        self.assertAlmostEqual(boulder.damage, 20 * 0.25)
        self.assertEqual(boulder.LIFETIME, 5.0)
        self.assertNotEqual(boulder.LIFETIME, Bullet.LIFETIME)

    def test_boulder_falls_on_first_hit(self):
        # Rolling Stone dừng lăn (rơi xuống) ngay khi trúng quái đầu tiên —
        # không xuyên qua nhiều địch (game_loop._fall_rolling_stones biến nó
        # thành 1 tảng đá tĩnh vĩnh viễn tại đây).
        from logic.rune.modifiers.rolling_stone_modifier import RollingStoneModifier
        rune = RollingStoneModifier()
        ctx = {'bullets': []}
        boulder = rune.trigger_once(0, 0, 100, ctx)
        e1, e2 = Enemy(0, 0), Enemy(10, 0)
        boulder.x, boulder.y = e1.x, e1.y
        boulder.on_hit(e1, {'enemies': [e1, e2], 'bullets': []})
        self.assertFalse(boulder.alive)

    def test_does_not_repeat_on_update(self):
        # Khác Furious Outburst: Rolling Stone chỉ nổ lúc spawn, không lặp lại
        from logic.rune.modifiers.rolling_stone_modifier import RollingStoneModifier
        slots = RuneSlots()
        slots.place(0, FireRune())
        slots.place(1, RollingStoneModifier())
        tree = slots.build_rune_tree()
        b = Bullet(0, 0, 100, 0, 20, tree)
        ctx = {'enemies': [], 'bullets': []}
        new_bullets = tree.on_fire(b, ctx)
        self.assertEqual(len(new_bullets), 1)
        tree.on_update(b, 2.0, ctx)   # bay 2 giay lien tuc
        self.assertEqual(len(ctx['bullets']), 0)   # RollingStone khong lap lai qua on_update


class TestSelfCentered(unittest.TestCase):
    """Self-Centered giờ là cast-graph modifier (neo vào Trigger/Spell), cho
    phép trên cả 4 hệ, Spawn Count +2 / Duration +150% / Orbit."""

    def test_allowed_on_all_4_elements(self):
        from logic.rune.rune_slots import slot_defs_for_rune
        from logic.rune.elements.wind_rune import WindRune
        from logic.rune.elements.lightning_rune import LightningRune
        from logic.rune.modifiers.self_centered_modifier import SelfCenteredModifier
        for elem_cls in (FireRune, IceRune, LightningRune, WindRune):
            e = elem_cls()
            s = RuneSlots(slot_defs_for_rune(e))
            s.set_core(e)
            self.assertTrue(s.can_place(1, SelfCenteredModifier()),
                            f"{elem_cls.__name__} phai cho phep SelfCentered")

    def test_on_spell_spawns_two_extra_and_orbits_player(self):
        from logic.rune.modifiers.self_centered_modifier import SelfCenteredModifier
        slots = RuneSlots()
        slots.place(0, FireRune())
        slots.place(1, SelfCenteredModifier())
        tree = slots.build_rune_tree()
        b = Bullet(0, 0, 100, 0, 20, tree)
        b.player_x, b.player_y = 0.0, 0.0
        extra = tree.on_fire(b, {'enemies': [], 'bullets': []})
        self.assertEqual(len(extra), 2)                 # Spawn Count +2
        for x in [b] + extra:                           # tất cả quay quanh player
            self.assertTrue(getattr(x, '_orbit', False))
        self.assertAlmostEqual(b.LIFETIME,
                               SelfCenteredModifier.BASE_DURATION * 2.5)  # Duration +150%

    def test_boomerang_not_orbited_but_still_multiplied(self):
        # Trên gió: boomerang (CAN_ORBIT=False) KHÔNG bị ép quay, chỉ +count.
        from logic.rune.elements.wind_rune import WindRune
        from logic.entities.wind_boomerang import WindBoomerang
        from logic.rune.modifiers.self_centered_modifier import SelfCenteredModifier
        tree = RuneTree()
        tree.set_element(WindRune())
        tree.modifiers = [SelfCenteredModifier()]
        b = WindBoomerang(0, 0, 200, 0, 30, tree)
        extra = tree.on_fire(b, {'bullets': [], 'active_effects': []})
        self.assertEqual(len(extra), 2)                 # +2 boomerang
        for x in [b] + extra:
            self.assertFalse(getattr(x, '_orbit', False))   # không quay

    def test_orbit_keeps_constant_radius(self):
        from logic.rune.modifiers.self_centered_modifier import SelfCenteredModifier
        slots = RuneSlots()
        slots.place(0, FireRune())
        slots.place(1, SelfCenteredModifier())
        tree = slots.build_rune_tree()
        b = Bullet(0, 0, 100, 0, 20, tree)
        b.player_x, b.player_y = 0.0, 0.0
        ctx = {'enemies': [], 'bullets': []}
        tree.on_fire(b, ctx)
        for _ in range(30):
            tree.on_update(b, 1 / 60, ctx)
            b.x += b.vx / 60
            b.y += b.vy / 60
        dist = math.hypot(b.x - b.player_x, b.y - b.player_y)
        self.assertAlmostEqual(dist, SelfCenteredModifier.ORBIT_RADIUS, delta=1.0)


class TestFlashOfSwordsAndSelfCentered(unittest.TestCase):
    """Đảo thứ tự Flash of Swords + Self-Centered (nối liên tiếp) trên hệ gió —
    đúng luật cast-graph 'neo vào Trigger gần nhất, else Spell gốc'."""

    def _fire_wind(self, parent_cls, child_cls):
        from logic.entities.wind_boomerang import WindBoomerang
        from logic.rune.elements.wind_rune import WindRune
        tree = RuneTree()
        tree.set_element(WindRune())
        p, c = parent_cls(), child_cls()
        p.add_child(c)
        tree.modifiers = [p]
        b = WindBoomerang(0, 0, 200, 0, 30.0, tree)
        extra = tree.on_fire(b, {'bullets': [], 'active_effects': []})
        allb = [b] + extra
        booms  = [x for x in allb if isinstance(x, WindBoomerang)]
        swords = [x for x in allb if getattr(x, 'visual_type', '') == 'sword_beam']
        return b, booms, swords

    def test_self_centered_parent_buffs_spell(self):
        # Self-Centered CHA → buff cây gió: 3 boomerang + Flash bắn theo mỗi spawn
        from logic.rune.modifiers.self_centered_modifier import SelfCenteredModifier
        from logic.rune.modifiers.flash_of_swords_trigger import FlashOfSwordsTrigger
        main, booms, swords = self._fire_wind(SelfCenteredModifier, FlashOfSwordsTrigger)
        self.assertEqual(len(booms), 3)                 # Spawn Count +2 lên SPELL
        self.assertEqual(len(swords), 3)                # Flash theo mỗi spawn
        for bm in booms:
            self.assertFalse(getattr(bm, '_orbit', False))  # boomerang không bị ép quay

    def test_flash_parent_buffs_trigger_swords_orbit_boomerang(self):
        # Flash CHA → Self-Centered buff TRIGGER: 1 boomerang + 3 tia kiếm quay
        # quanh boomerang, duration +150%.
        from logic.rune.modifiers.self_centered_modifier import SelfCenteredModifier
        from logic.rune.modifiers.flash_of_swords_trigger import FlashOfSwordsTrigger
        main, booms, swords = self._fire_wind(FlashOfSwordsTrigger, SelfCenteredModifier)
        self.assertEqual(len(booms), 1)                 # cây gió KHÔNG bị buff
        self.assertEqual(len(swords), 3)                # Flash tự nhân x3
        for s in swords:
            self.assertTrue(getattr(s, '_orbit', False))
            self.assertIs(s._orbit_target, main)        # quay quanh boomerang
            self.assertAlmostEqual(s.LIFETIME,
                                   FlashOfSwordsTrigger.BASE_DURATION * 2.5)  # +150%

    def test_flash_alone_one_orbiting_sword(self):
        from logic.rune.modifiers.flash_of_swords_trigger import FlashOfSwordsTrigger
        from logic.rune.elements.wind_rune import WindRune
        from logic.entities.wind_boomerang import WindBoomerang
        tree = RuneTree()
        tree.set_element(WindRune())
        tree.modifiers = [FlashOfSwordsTrigger()]
        b = WindBoomerang(0, 0, 200, 0, 30.0, tree)
        extra = tree.on_fire(b, {'bullets': [], 'active_effects': []})
        swords = [x for x in extra if getattr(x, 'visual_type', '') == 'sword_beam']
        self.assertEqual(len(swords), 1)
        self.assertTrue(swords[0]._orbit)
        self.assertIs(swords[0]._orbit_target, b)
        # Damage 20% của base
        self.assertIn(round(swords[0].damage, 2), (6.0, 12.0))  # 30*0.2, hoặc crit x2

    def test_flash_works_on_all_4_elements(self):
        from logic.rune.rune_slots import slot_defs_for_rune
        from logic.rune.elements.lightning_rune import LightningRune
        from logic.rune.elements.wind_rune import WindRune
        from logic.rune.modifiers.flash_of_swords_trigger import FlashOfSwordsTrigger
        for elem_cls in (FireRune, IceRune, LightningRune, WindRune):
            e = elem_cls()
            s = RuneSlots(slot_defs_for_rune(e))
            s.set_core(e)
            self.assertTrue(s.can_place(1, FlashOfSwordsTrigger()),
                            f"{elem_cls.__name__} phai cho phep Flash of Swords")


class TestDestructivePath(unittest.TestCase):
    def _tree(self):
        from logic.rune.modifiers.destructive_path_modifier import DestructivePathModifier
        slots = RuneSlots()
        slots.place(0, FireRune())
        slots.place(1, DestructivePathModifier())
        return slots.build_rune_tree()

    def test_on_fire_leaves_one_patch_with_zero_damage(self):
        tree = self._tree()
        b = Bullet(0, 0, 100, 0, 20, tree)
        ctx = {'enemies': [], 'bullets': [], 'active_effects': []}
        tree.on_fire(b, ctx)
        self.assertEqual(len(ctx['active_effects']), 1)
        patch = ctx['active_effects'][0]
        self.assertEqual(patch.damage, 0.0)

    def test_patch_duration_matches_trail_duration(self):
        from logic.rune.modifiers.destructive_path_modifier import DestructivePathModifier
        tree = self._tree()
        b = Bullet(0, 0, 100, 0, 20, tree)
        ctx = {'enemies': [], 'bullets': [], 'active_effects': []}
        tree.on_fire(b, ctx)
        patch = ctx['active_effects'][0]
        self.assertAlmostEqual(patch.trail_duration, DestructivePathModifier.TRAIL_DURATION, places=2)

    def test_on_update_leaves_one_continuous_trail_growing_by_distance(self):
        # Thiết kế mới: KHÔNG sinh nhiều active_effects rời rạc nữa — chỉ 1
        # FireTrailEffect duy nhất, "dài" thêm ra bằng cách nối thêm điểm mỗi
        # khi đạn đã bay đủ TRAIL_INTERVAL px (add_point() gọi qua on_update,
        # cần bullet.x/y THẬT SỰ đổi giữa các lần gọi — dùng b.update() mô
        # phỏng đúng vòng lặp thật thay vì gọi tree.on_update() 1 phát to).
        tree = self._tree()
        b = Bullet(0, 0, 100, 0, 20, tree)
        ctx = {'enemies': [], 'bullets': [], 'active_effects': []}
        tree.on_fire(b, ctx)
        self.assertEqual(len(ctx['active_effects']), 1)
        trail = ctx['active_effects'][0]
        self.assertEqual(len(trail.points), 1)
        dt = 1 / 60.0
        for _ in range(60):   # 400px/s * 1s = 400px quãng đường
            b.update(dt, ctx)
        self.assertEqual(len(ctx['active_effects']), 1)   # vẫn chỉ 1 effect
        self.assertGreater(len(trail.points), 10)         # nhưng "dài" ra nhiều điểm

    def test_patch_applies_burn_when_active(self):
        from logic.rune.modifiers.destructive_path_modifier import DestructivePathModifier
        rune = DestructivePathModifier()
        ctx = {'active_effects': []}
        trail = rune._spawn_trail(0, 0, ctx)
        enemy = Enemy(0, 0)
        hits = trail.check_hits([enemy], None)
        self.assertEqual(len(hits), 1)


class TestFreneticEnergyAndPerfectStorm(unittest.TestCase):
    """Luật 'neo vào Trigger gần nhất phía trên, else Spell gốc'
    (Echoes of Mystralia) — verify đúng ví dụ thực tế: đảo thứ tự Frenetic/Storm
    cho ra số storm/đạn chính khác nhau."""

    def _tree(self, parent_cls, child_cls):
        from logic.rune.rune_slots import SLOT_DEFS_FIRE
        slots = RuneSlots(SLOT_DEFS_FIRE)
        slots.set_core(FireRune())
        slots.place(3, parent_cls())
        slots.place(4, child_cls())
        return slots.build_rune_tree()

    def test_storm_parent_frenetic_child_gives_4_storm_1_main(self):
        from logic.rune.modifiers.perfect_storm_modifier import PerfectStormModifier
        from logic.rune.modifiers.frenetic_energy_modifier import FreneticEnergyModifier
        tree = self._tree(PerfectStormModifier, FreneticEnergyModifier)
        b = Bullet(0, 0, 100, 0, 10, tree)
        ctx = {'bullets': [], 'active_effects': []}
        new_bullets = tree.on_fire(b, ctx)
        self.assertEqual(len(ctx['active_effects']), 4)   # Frenetic gan vao Storm (Spawn Count +3)
        self.assertEqual(1 + len(new_bullets), 1)          # Spell goc khong bi dung toi

    def test_frenetic_parent_storm_child_gives_4_storm_4_main(self):
        from logic.rune.modifiers.perfect_storm_modifier import PerfectStormModifier
        from logic.rune.modifiers.frenetic_energy_modifier import FreneticEnergyModifier
        tree = self._tree(FreneticEnergyModifier, PerfectStormModifier)
        b = Bullet(0, 0, 100, 0, 10, tree)
        ctx = {'bullets': [], 'active_effects': []}
        new_bullets = tree.on_fire(b, ctx)
        self.assertEqual(1 + len(new_bullets), 4)          # Frenetic gan vao Spell goc (Spawn Count +3)
        self.assertEqual(len(ctx['active_effects']), 4)    # Storm fire theo tung spawn

    def test_frenetic_works_on_all_4_elements(self):
        # Ca Fire/Wind (Bullet/WindBoomerang qua rune_tree.on_fire) va Ice/
        # Lightning (khong co Bullet object, cast graph duoc tinh thu cong
        # trong game_loop._release_ice_charge/_channel_lightning_attack) deu
        # cho phep — dung nhu nguyen tac cua Echoes of Mystralia.
        from logic.rune.rune_slots import slot_defs_for_rune
        from logic.rune.elements.ice_rune import IceRune
        from logic.rune.elements.lightning_rune import LightningRune
        from logic.rune.elements.wind_rune import WindRune
        from logic.rune.modifiers.frenetic_energy_modifier import FreneticEnergyModifier
        for elem_cls in (FireRune, IceRune, LightningRune, WindRune):
            e = elem_cls()
            s = RuneSlots(slot_defs_for_rune(e))
            s.set_core(e)
            self.assertTrue(s.can_place(1, FreneticEnergyModifier()),
                            f"{elem_cls.__name__} phai cho phep FreneticEnergy")

    def test_perfect_storm_simple_trigger_once(self):
        """Duong don gian (Lightning/Ice tuc thoi) — 1 lan goi = 1 VortexZone."""
        from logic.rune.modifiers.perfect_storm_modifier import PerfectStormModifier
        rune = PerfectStormModifier()
        ctx = {'active_effects': []}
        result = rune.trigger_once(0, 0, 100, ctx)
        self.assertIsNone(result)
        self.assertEqual(len(ctx['active_effects']), 1)
        zone = ctx['active_effects'][0]
        self.assertAlmostEqual(zone.damage, 100 * 0.40)

    def test_vortex_pulls_enemy_toward_center(self):
        from logic.rune.modifiers.perfect_storm_modifier import PerfectStormModifier
        rune = PerfectStormModifier()
        ctx = {'active_effects': []}
        rune.trigger_once(0, 0, 100, ctx)
        zone = ctx['active_effects'][0]
        enemy = Enemy(80, 0)   # dung trong ban kinh vung
        dist_before = enemy.x
        zone.apply_pull([enemy], None)   # ap/refresh StatusEffect 'vortex' len enemy
        # player dat ngay tam von (0,0) de "chase" va "pull" khong triet tieu nhau
        enemy.update(0.1, player_x=0.0, player_y=0.0)
        self.assertLess(enemy.x, dist_before)   # bi hut ve gan tam (0,0) hon


class TestStarsAligned(unittest.TestCase):
    """Cung luat neo nhu Frenetic Energy nhung pattern 'line' + speed/size mult."""

    def test_attached_to_root_spell_line_pattern(self):
        from logic.rune.modifiers.stars_aligned_modifier import StarsAlignedModifier
        from logic.rune.rune_slots import SLOT_DEFS_FIRE
        slots = RuneSlots(SLOT_DEFS_FIRE)
        slots.set_core(FireRune())
        slots.place(3, StarsAlignedModifier())
        tree = slots.build_rune_tree()
        b = Bullet(0, 0, 100, 0, 10, tree)
        speed0 = math.hypot(b.vx, b.vy)
        radius0 = b.radius
        new_bullets = tree.on_fire(b, {'bullets': [], 'active_effects': []})

        self.assertEqual(1 + len(new_bullets), 3)                  # Spawn Count +2
        self.assertAlmostEqual(b.damage, 10 * 0.7)                  # Damage x0.7
        self.assertAlmostEqual(math.hypot(b.vx, b.vy), speed0 * 1.3)  # Speed x1.3
        self.assertAlmostEqual(b.radius, radius0 * 0.5)             # Size x0.5
        # Ca 3 vien bay CUNG huong (dan hang, khong toa goc nhu cone)
        for nb in new_bullets:
            self.assertAlmostEqual(nb.vy, b.vy, places=3)
        # Khong con vien nao trung vi tri (dan hang lech nhau)
        ys = sorted([b.y] + [nb.y for nb in new_bullets])
        self.assertEqual(len(set(round(y, 3) for y in ys)), 3)

    def test_attached_to_storm_scales_size_and_pull(self):
        from logic.rune.modifiers.stars_aligned_modifier import StarsAlignedModifier
        from logic.rune.modifiers.perfect_storm_modifier import PerfectStormModifier
        from logic.rune.rune_slots import SLOT_DEFS_FIRE
        slots = RuneSlots(SLOT_DEFS_FIRE)
        slots.set_core(FireRune())
        slots.place(3, PerfectStormModifier())
        slots.place(4, StarsAlignedModifier())
        tree = slots.build_rune_tree()
        b = Bullet(0, 0, 100, 0, 10, tree)
        ctx = {'bullets': [], 'active_effects': []}
        tree.on_fire(b, ctx)

        self.assertEqual(len(ctx['active_effects']), 3)   # Spawn Count +2 ap len Storm
        base_radius = PerfectStormModifier.SIZE * PerfectStormModifier.SIZE_TO_PX
        base_pull   = PerfectStormModifier.PULL_STRENGTH
        for zone in ctx['active_effects']:
            self.assertAlmostEqual(zone.AoE_RADIUS, base_radius * 0.5)     # Size x0.5
            self.assertAlmostEqual(zone.pull_strength, base_pull * 1.3)   # Speed x1.3

    def test_works_on_all_4_elements(self):
        from logic.rune.rune_slots import slot_defs_for_rune
        from logic.rune.elements.ice_rune import IceRune
        from logic.rune.elements.lightning_rune import LightningRune
        from logic.rune.elements.wind_rune import WindRune
        from logic.rune.modifiers.stars_aligned_modifier import StarsAlignedModifier
        for elem_cls in (FireRune, IceRune, LightningRune, WindRune):
            e = elem_cls()
            s = RuneSlots(slot_defs_for_rune(e))
            s.set_core(e)
            self.assertTrue(s.can_place(1, StarsAlignedModifier()),
                            f"{elem_cls.__name__} phai cho phep StarsAligned")


class TestFreneticStarsAlignedCombo(unittest.TestCase):
    """2 rune cast-graph cung gan vao 1 nhanh (khong Trigger nao o giua) — cong
    dồn spawn_count/damage_mult (giao hoan, khong phu thuoc thu tu), va MOI
    rune GIU DUNG doi hinh rieng cua no (Frenetic toa cone, StarsAligned dan
    hang) du dung o vi tri cha hay con — khong con rune nao "ghi de" doi hinh
    cua rune kia nua."""

    def _tree(self, parent_cls, child_cls):
        from logic.rune.rune_slots import SLOT_DEFS_FIRE
        slots = RuneSlots(SLOT_DEFS_FIRE)
        slots.set_core(FireRune())
        slots.place(3, parent_cls())
        slots.place(4, child_cls())
        return slots.build_rune_tree()

    def test_spawn_count_damage_speed_size_stack_regardless_of_order(self):
        from logic.rune.modifiers.frenetic_energy_modifier import FreneticEnergyModifier
        from logic.rune.modifiers.stars_aligned_modifier import StarsAlignedModifier
        for parent_cls, child_cls in (
            (FreneticEnergyModifier, StarsAlignedModifier),
            (StarsAlignedModifier, FreneticEnergyModifier),
        ):
            tree = self._tree(parent_cls, child_cls)
            b = Bullet(0, 0, 100, 0, 10, tree)
            speed0 = math.hypot(b.vx, b.vy)
            new_bullets = tree.on_fire(b, {'bullets': [], 'active_effects': []})
            self.assertEqual(1 + len(new_bullets), 6)             # 1 + 3 + 2
            self.assertAlmostEqual(b.damage, 10 * 0.8 * 0.7)      # giao hoan
            self.assertAlmostEqual(math.hypot(b.vx, b.vy), speed0 * 1.3)
            self.assertAlmostEqual(b.radius, Bullet.RADIUS * 0.5)

    def test_each_modifier_keeps_its_own_formation_regardless_of_order(self):
        """6 vien = 1 goc (thang) + 3 cua Frenetic (toa cone, cung vi tri,
        huong bay lech ngau nhien) + 2 cua StarsAligned (dan hang, cung huong
        bay, vi tri lech nhau) — bat ke Frenetic hay StarsAligned dung cha/con."""
        from logic.rune.modifiers.frenetic_energy_modifier import FreneticEnergyModifier
        from logic.rune.modifiers.stars_aligned_modifier import StarsAlignedModifier

        for parent_cls, child_cls in (
            (FreneticEnergyModifier, StarsAlignedModifier),
            (StarsAlignedModifier, FreneticEnergyModifier),
        ):
            tree = self._tree(parent_cls, child_cls)
            b = Bullet(0, 0, 100, 0, 10, tree)
            new_bullets = tree.on_fire(b, {'bullets': [], 'active_effects': []})
            all_bullets = [b] + new_bullets

            same_pos_same_dir   = 0   # vien goc (thang, khong lech gi)
            same_pos_diff_dir   = 0   # 3 vien cua Frenetic (toa cone)
            diff_pos_same_dir   = 0   # 2 vien cua StarsAligned (dan hang)
            for nb in all_bullets:
                same_pos = abs(nb.y - b.y) < 1e-6
                same_dir = abs(nb.vy - b.vy) < 1e-6
                if same_pos and same_dir:
                    same_pos_same_dir += 1
                elif same_pos and not same_dir:
                    same_pos_diff_dir += 1
                elif not same_pos and same_dir:
                    diff_pos_same_dir += 1

            self.assertEqual(same_pos_same_dir, 1, f"{parent_cls.__name__} cha")
            self.assertEqual(same_pos_diff_dir, 3, f"{parent_cls.__name__} cha")  # Frenetic
            self.assertEqual(diff_pos_same_dir, 2, f"{parent_cls.__name__} cha")  # StarsAligned


class TestOrderInvariants(unittest.TestCase):
    """Bộ test BẤT BIẾN theo tổ hợp — quét TỰ ĐỘNG cả ma trận rune × thứ tự,
    thay vì spot-check từng case. Đây là thứ biến 'đã chốt' thành thứ verify
    được: mọi tổ hợp rune CHƯA từng thử tay vẫn được kiểm trước.

    Luật (canonical) của hệ ghép rune:
      1. Rune gắn vào CÙNG 1 node (anh em) → thứ tự KHÔNG được đổi kết quả
         (giao hoán). Chỉ cấu trúc CHA-CON (neo vào Trigger) mới mang ý nghĩa.
      2. Buff + Trigger: sát thương/hiệu ứng Trigger phun ra phải bằng nhau dù
         buff đứng cha hay con ('1.5x0.2 kiểu gì cũng vậy').
      3. Mỗi rune giữ ĐÚNG đội hình riêng của mình (cone/line) bất kể ai cha/con.

    Tạo RuneTree TRỰC TIẾP (bỏ qua slot/ngân sách) để test đúng phần lõi
    RuneTree.on_fire — quy tắc slot đã có test riêng."""

    # Runes tham gia on_fire theo cách có thể sinh/đổi đạn — tất cả PHẢI giao
    # hoán khi đứng anh em (sau khi vá ON_FIRE_PRIORITY).
    def _sweep_runes(self):
        from logic.rune.modifiers.heavy_hitter_modifier import HeavyHitterModifier
        from logic.rune.modifiers.lightened_heart_modifier import LightenedHeartModifier
        from logic.rune.modifiers.piercing_eyes_modifier import PiercingEyesModifier
        from logic.rune.modifiers.frenetic_energy_modifier import FreneticEnergyModifier
        from logic.rune.modifiers.stars_aligned_modifier import StarsAlignedModifier
        from logic.rune.modifiers.furious_outburst_modifier import FuriousOutburstModifier
        from logic.rune.modifiers.rolling_stone_modifier import RollingStoneModifier
        from logic.rune.modifiers.perfect_storm_modifier import PerfectStormModifier
        return [
            HeavyHitterModifier, LightenedHeartModifier, PiercingEyesModifier,
            FreneticEnergyModifier, StarsAlignedModifier,
            TwistOfFateModifier, FuriousOutburstModifier, RollingStoneModifier,
            PerfectStormModifier,
        ]

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _sig_siblings(self, classes, element_cls=FireRune):
        """Bắn 1 viên đạn thật với `classes` làm rune anh em (phẳng, cùng gắn
        vào Spell gốc). Trả về chữ ký CHỈ gồm các trường TẤT ĐỊNH (không phụ
        thuộc random cone-jitter) → so sánh chính xác được."""
        random.seed(2024)
        tree = RuneTree()
        tree.set_element(element_cls())
        tree.modifiers = [c() for c in classes]
        b = Bullet(0, 0, 100, 0, 20.0, tree)
        ctx = {'bullets': [], 'active_effects': [], 'enemies': []}
        extra = tree.on_fire(b, ctx)
        return (
            1 + len(extra),                                             # tổng số đạn
            round(b.damage, 6),                                        # dmg viên chính
            round(math.hypot(b.vx, b.vy), 4),                          # tốc độ viên chính
            round(b.radius, 6),                                        # size viên chính
            getattr(b, 'pierce_remaining', 0),                         # xuyên
            tuple(sorted(round(x.damage, 4) for x in extra)),          # multiset dmg đạn phụ
            tuple(sorted((round(x.x, 2), round(x.y, 2)) for x in extra)),  # multiset vị trí đạn phụ
            len(ctx['active_effects']),                                # số AoE (vd Vortex)
            tuple(sorted(round(getattr(e, 'damage', 0), 4)
                         for e in ctx['active_effects'])),             # multiset dmg AoE
        )

    def _sig_nest(self, parent_cls, child_cls):
        """parent -> child (child là con của parent)."""
        random.seed(99)
        tree = RuneTree()
        tree.set_element(FireRune())
        p, c = parent_cls(), child_cls()
        p.add_child(c)
        tree.modifiers = [p]
        b = Bullet(0, 0, 100, 0, 20.0, tree)
        ctx = {'bullets': [], 'active_effects': [], 'enemies': []}
        extra = tree.on_fire(b, ctx)
        return (
            1 + len(extra),
            round(b.damage, 4),
            tuple(sorted(round(x.damage, 4) for x in extra)),
            len(ctx['active_effects']),
            tuple(sorted(round(getattr(e, 'damage', 0), 4)
                         for e in ctx['active_effects'])),
        )

    # ── Invariant 1: mọi CẶP anh em phải giao hoán (quét toàn ma trận) ────────

    def test_all_sibling_pairs_commute(self):
        runes = self._sweep_runes()
        for a, b in itertools.combinations(runes, 2):
            forward  = self._sig_siblings([a, b])
            backward = self._sig_siblings([b, a])
            self.assertEqual(
                forward, backward,
                f"Thứ tự anh em đổi kết quả: {a.__name__} + {b.__name__}\n"
                f"  {a.__name__}->{b.__name__}: {forward}\n"
                f"  {b.__name__}->{a.__name__}: {backward}")

    # ── Invariant 1b: mọi BỘ-BA anh em, MỌI hoán vị đều cho cùng kết quả ──────

    def test_sibling_triples_commute_all_permutations(self):
        runes = self._sweep_runes()
        for triple in itertools.combinations(runes, 3):
            sigs = {self._sig_siblings(list(p))
                    for p in itertools.permutations(triple)}
            self.assertEqual(
                len(sigs), 1,
                f"Bộ ba {[c.__name__ for c in triple]} có {len(sigs)} kết quả "
                f"khác nhau theo hoán vị (phải = 1)")

    # ── Invariant 2: buff + spawner/trigger anh em → buff LUÔN áp (thứ tự slot
    #    không đổi được) — chốt lại đúng lỗ hổng đã vá ────────────────────────

    def test_buff_applies_to_spawner_regardless_of_order(self):
        from logic.rune.modifiers.heavy_hitter_modifier import HeavyHitterModifier
        from logic.rune.modifiers.furious_outburst_modifier import FuriousOutburstModifier
        from logic.rune.modifiers.rolling_stone_modifier import RollingStoneModifier
        cases = [
            (FuriousOutburstModifier, (6.0,)),      # fireball = 20 * 1.5 * 0.2
            (RollingStoneModifier, (7.5,)),         # boulder  = 20 * 1.5 * 0.25
        ]
        for spawner_cls, expected in cases:
            for order in ([HeavyHitterModifier, spawner_cls],
                          [spawner_cls, HeavyHitterModifier]):
                random.seed(1)
                tree = RuneTree()
                tree.set_element(FireRune())
                tree.modifiers = [c() for c in order]
                b = Bullet(0, 0, 100, 0, 20.0, tree)
                extra = tree.on_fire(b, {'bullets': [], 'active_effects': []})
                got = tuple(sorted(round(x.damage, 4) for x in extra))
                self.assertEqual(
                    got, expected,
                    f"{[c.__name__ for c in order]}: spawn dmg {got} != {expected} "
                    f"(buff phải áp cho spawner bất kể thứ tự)")

    # ── Invariant 3: buff + Trigger neo nhau → NESTING CÓ Ý NGHĨA ──────────────
    #    Sát thương ĐẠN PHỤ trigger phun ra bằng nhau dù buff cha/con (1.5x0.2 =
    #    0.2x1.5), NHƯNG với trigger tự-mang-đạn-phụ (OWNS_SUBTREE: Furious
    #    Outburst, Rolling Stone), buff đặt TRÊN trigger còn buff luôn ĐẠN CHÍNH,
    #    buff đặt DƯỚI chỉ buff đạn phụ. Cast-graph trigger (Perfect Storm) thì
    #    đối xứng hoàn toàn (buff áp lên đạn chính ở cả 2 cách).

    def test_buff_trigger_nesting_semantics(self):
        from logic.rune.modifiers.heavy_hitter_modifier import HeavyHitterModifier
        from logic.rune.modifiers.furious_outburst_modifier import FuriousOutburstModifier
        from logic.rune.modifiers.rolling_stone_modifier import RollingStoneModifier
        from logic.rune.modifiers.perfect_storm_modifier import PerfectStormModifier

        # _sig_nest → (n, main_dmg, spawn_dmgs, n_aoe, aoe_dmgs); đạn phụ nằm ở
        # spawn_dmgs (đạn) hoặc aoe_dmgs (vortex).
        def spawn_dmg(sig):
            return sig[2] or sig[4]

        # Trigger OWNS_SUBTREE: đạn phụ đối xứng, đạn chính KHÔNG.
        for trigger_cls in (FuriousOutburstModifier, RollingStoneModifier):
            ab = self._sig_nest(HeavyHitterModifier, trigger_cls)   # buff cha
            ba = self._sig_nest(trigger_cls, HeavyHitterModifier)   # buff con
            self.assertEqual(
                spawn_dmg(ab), spawn_dmg(ba),
                f"{trigger_cls.__name__}: dmg đạn phụ phải bằng nhau (1.5x0.2)\n"
                f"  HH cha: {ab}\n  {trigger_cls.__name__} cha: {ba}")
            self.assertGreater(
                ab[1], ba[1],
                f"{trigger_cls.__name__}: buff TRÊN trigger phải buff đạn chính")
            self.assertEqual(
                ba[1], 20.0,
                f"{trigger_cls.__name__}: buff DƯỚI trigger KHÔNG được đụng đạn chính")

        # Cast-graph trigger (không OWNS_SUBTREE): đối xứng hoàn toàn.
        ab = self._sig_nest(HeavyHitterModifier, PerfectStormModifier)
        ba = self._sig_nest(PerfectStormModifier, HeavyHitterModifier)
        self.assertEqual(
            ab, ba,
            f"PerfectStorm: cast-graph phải đối xứng\n  HH cha: {ab}\n  PS cha: {ba}")

    # ── Invariant 4: cast-graph tất định như nhau trên CẢ 4 HỆ ───────────────
    #    (resolve_cast_graph chỉ đọc modifiers → độc lập element; test này chốt
    #     rằng không hệ nào bị 'bỏ rơi' — đúng nỗi lo 'chỉ Fire mới chạy').

    def test_cast_graph_identical_across_all_4_elements(self):
        from logic.rune.elements.lightning_rune import LightningRune
        from logic.rune.elements.wind_rune import WindRune
        from logic.rune.modifiers.frenetic_energy_modifier import FreneticEnergyModifier
        from logic.rune.modifiers.stars_aligned_modifier import StarsAlignedModifier

        def resolve(element_cls, order):
            tree = RuneTree()
            tree.set_element(element_cls())
            tree.modifiers = [c() for c in order]
            root, _tp, _tr, _order = tree.resolve_cast_graph()
            return (round(root.damage_mult, 6), round(root.speed_mult, 6),
                    round(root.size_mult, 6),
                    tuple(sorted((n, p, round(s, 4)) for n, p, s in root.batches)))

        elements = [FireRune, IceRune, LightningRune, WindRune]
        orders = [
            [FreneticEnergyModifier, StarsAlignedModifier],
            [StarsAlignedModifier, FreneticEnergyModifier],
        ]
        sigs = {resolve(e, o) for e in elements for o in orders}
        self.assertEqual(
            len(sigs), 1,
            f"Cast-graph khác nhau giữa các hệ/thứ tự (phải đồng nhất): {sigs}")

    # ── Invariant 5: mỗi rune giữ đội hình riêng (line vs cone) trong sweep ───

    def test_stars_aligned_batch_is_always_line(self):
        """Dù đứng cùng bao nhiêu rune khác, Stars Aligned luôn đóng góp đúng
        1 batch 'line' của riêng nó (song song), không bị nuốt/đổi thành cone."""
        from logic.rune.modifiers.stars_aligned_modifier import StarsAlignedModifier
        from logic.rune.modifiers.frenetic_energy_modifier import FreneticEnergyModifier
        for others in ([], [FreneticEnergyModifier], [FreneticEnergyModifier, TwistOfFateModifier]):
            for order in itertools.permutations([StarsAlignedModifier] + others):
                tree = RuneTree()
                tree.set_element(FireRune())
                tree.modifiers = [c() for c in order]
                root, _tp, _tr, _o = tree.resolve_cast_graph()
                lines = [b for b in root.batches if b[1] == 'line']
                self.assertEqual(len(lines), 1,
                                 f"{[c.__name__ for c in order]}: batch 'line' phải đúng 1")
                self.assertEqual(lines[0][0], StarsAlignedModifier.SPAWN_COUNT_DELTA)


class TestStarsAlignedParallelAllElements(unittest.TestCase):
    """Stars Aligned PHẢI cast dạng SONG SONG (dàn hàng: cùng hướng, lệch vị
    trí vuông góc) trên CẢ 4 HỆ — không được ra cone/quạt góc ở bất kỳ hệ nào.
    Chạy qua đúng đường game_loop thật (Fire/Wind: RuneTree.on_fire; Ice:
    _release_ice_charge; Lightning: _channel_lightning_attack)."""

    @classmethod
    def setUpClass(cls):
        import os
        os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
        os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

    def _game_with(self, element_cls):
        from ui.game_loop import GameLoop
        from logic.rune.modifiers.stars_aligned_modifier import StarsAlignedModifier
        gl = GameLoop()
        gl.player.setup_spells([element_cls(), element_cls()])
        sp = gl.player.spells[0]
        self.assertTrue(sp.rune_slots.place(1, StarsAlignedModifier()))
        gl.player.rebuild_all_spells()
        gl.player.set_active_spell(0)
        gl.player.x, gl.player.y = 0.0, 0.0
        return gl, sp

    def _assert_projectile_parallel(self, element_cls, bullet_cls):
        gl, sp = self._game_with(element_cls)
        b = bullet_cls(0, 0, 100, 0, 20.0, sp.rune_tree)
        extra = sp.rune_tree.on_fire(b, {'bullets': [], 'active_effects': []})
        allb = [b] + extra
        dirs = {(round(x.vx, 3), round(x.vy, 3)) for x in allb}
        ys   = {round(x.y, 3) for x in allb}
        self.assertEqual(len(dirs), 1, f"{element_cls.__name__}: các viên phải CÙNG hướng")
        self.assertEqual(len(ys), len(allb), f"{element_cls.__name__}: vị trí phải lệch nhau")

    def test_fire_parallel(self):
        self._assert_projectile_parallel(FireRune, Bullet)

    def test_wind_parallel(self):
        from logic.rune.elements.wind_rune import WindRune
        from logic.entities.wind_boomerang import WindBoomerang
        self._assert_projectile_parallel(WindRune, WindBoomerang)

    def test_ice_spikes_parallel_not_cone(self):
        gl, sp = self._game_with(IceRune)
        ice_rune = sp.rune_tree.element
        base_attack = ice_rune.build_charge_attack(0, 0, 100, 0, 0.6)

        line_calls, cone_calls = [], []
        orig_line, orig_cone = gl._build_ice_attack_at, gl._build_split_ice_attack
        gl._build_ice_attack_at = lambda r, sx, sy, a, h: (
            line_calls.append((round(sx, 2), round(sy, 2), round(a, 4))) or orig_line(r, sx, sy, a, h))
        gl._build_split_ice_attack = lambda r, ba, off, h: (
            cone_calls.append(off) or orig_cone(r, ba, off, h))

        gl.ice_charge = {"rune": ice_rune, "spell": sp,
                         "attacks": [base_attack], "attack": base_attack, "held": 0.6}
        gl._release_ice_charge()

        from logic.rune.modifiers.stars_aligned_modifier import StarsAlignedModifier
        self.assertEqual(len(line_calls), StarsAlignedModifier.SPAWN_COUNT_DELTA)
        self.assertEqual(len(cone_calls), 0, "Ice không được ra spike dạng cone")
        self.assertEqual(len({a for _sx, _sy, a in line_calls}), 1, "spike phải cùng hướng")
        self.assertEqual(len({(sx, sy) for sx, sy, _a in line_calls}), len(line_calls),
                         "spike phải lệch vị trí (song song)")

    def test_lightning_beams_parallel_not_cone(self):
        from logic.rune.elements.lightning_rune import LightningRune
        from ui.game_loop import LIGHTNING_CAST_RELEASE_FRAME, LIGHTNING_CAST_FRAME_MS
        gl, sp = self._game_with(LightningRune)
        beams = []
        orig = gl._set_primary_lightning_beam
        gl._set_primary_lightning_beam = lambda sx, sy, ex, ey, beam_id=0, vortex=False: (
            beams.append((sx, sy, ex, ey)) or orig(sx, sy, ex, ey, beam_id=beam_id, vortex=vortex))
        gl._lightning_channel_active = False

        # Tia chỉ thực sự xuất hiện SAU khi charge qua windup (xem
        # LIGHTNING_CAST_RELEASE_FRAME) — giữ chuột đủ nhiều frame như
        # gameplay thật thay vì gọi 1 lần duy nhất.
        dt = 1 / 60
        release_time = LIGHTNING_CAST_RELEASE_FRAME * LIGHTNING_CAST_FRAME_MS / 1000.0
        steps = int(release_time / dt) + 2
        for _ in range(steps):
            beams.clear()
            gl._channel_lightning_attack(100.0, 0.0, dt)

        def unit_dir(sx, sy, ex, ey):
            d = math.hypot(ex - sx, ey - sy)
            return (round((ex - sx) / d, 4), round((ey - sy) / d, 4))

        self.assertEqual(len(beams), 3, "1 beam gốc + 2 beam Stars Aligned")
        self.assertEqual(len({unit_dir(*b) for b in beams}), 1, "beam phải CÙNG hướng")
        self.assertEqual(len({(round(b[0], 2), round(b[1], 2)) for b in beams}), len(beams),
                         "beam phải lệch gốc (song song)")


class TestRuneTaxonomy(unittest.TestCase):
    """Phân loại rune (Composite taxonomy): Element / Modifier / Trigger.
    Đây là 'nguồn sự thật' — mọi rune trong ALL_RUNES phải được xếp loại rõ
    ràng, và phân loại phải nhất quán với cơ chế (cast-graph trigger, trigger_once)."""

    # Danh sách chốt cứng — thêm rune mới mà quên khai báo IS_TRIGGER sẽ làm
    # test này đỏ (bắt lỗi trước khi trôi).
    EXPECTED_TRIGGERS = {
        "FuriousOutburstModifier", "RollingStoneModifier",
        "PerfectStormModifier", "FlashOfSwordsTrigger",
    }

    def test_elements_are_kind_element(self):
        from logic.rune.elements.lightning_rune import LightningRune
        from logic.rune.elements.wind_rune import WindRune
        for cls in (FireRune, IceRune, LightningRune, WindRune):
            self.assertEqual(cls().get_rune_kind(), 'element')

    def test_every_rune_classified_modifier_or_trigger(self):
        from logic.leveling.level_manager import ALL_RUNES
        for cls in ALL_RUNES:
            kind = cls().get_rune_kind()
            self.assertIn(kind, ('modifier', 'trigger'),
                          f"{cls.__name__} chưa được phân loại rõ ràng")

    def test_triggers_match_expected_set(self):
        from logic.leveling.level_manager import ALL_RUNES
        triggers = {cls.__name__ for cls in ALL_RUNES if cls().get_rune_kind() == 'trigger'}
        self.assertEqual(triggers, self.EXPECTED_TRIGGERS)

    def test_triggers_have_trigger_once_and_condition(self):
        from logic.leveling.level_manager import ALL_RUNES
        for cls in ALL_RUNES:
            r = cls()
            if r.get_rune_kind() == 'trigger':
                self.assertTrue(callable(getattr(r, 'trigger_once', None)),
                                f"Trigger {cls.__name__} phải có trigger_once()")
                self.assertTrue(r.get_trigger_label().startswith("Triggered"),
                                f"Trigger {cls.__name__} phải có nhãn 'Triggered on ...'")

    def test_cast_graph_triggers_are_triggers(self):
        # Mọi rune bật IS_CAST_GRAPH_TRIGGER bắt buộc cũng là Trigger.
        from logic.leveling.level_manager import ALL_RUNES
        for cls in ALL_RUNES:
            r = cls()
            if getattr(r, 'IS_CAST_GRAPH_TRIGGER', False):
                self.assertEqual(r.get_rune_kind(), 'trigger',
                                 f"{cls.__name__} là cast-graph trigger nhưng chưa IS_TRIGGER")

    def test_destructive_path_is_modifier_without_trigger_once(self):
        # Dùng on_fire/on_update (Fire/Wind) + leave_trail_along() riêng
        # (Ice/Lightning, game_loop tự gọi) — KHÔNG dùng cơ chế trigger_once
        # chung nữa, nên phải bị loại khỏi _find_triggerable_modifiers().
        from logic.rune.modifiers.destructive_path_modifier import DestructivePathModifier
        r = DestructivePathModifier()
        self.assertFalse(hasattr(r, 'trigger_once'))
        self.assertTrue(callable(getattr(r, 'leave_trail_along', None)))
        self.assertEqual(r.get_rune_kind(), 'modifier')
        self.assertEqual(r.get_trigger_label(), "")


if __name__ == '__main__':
    unittest.main()
