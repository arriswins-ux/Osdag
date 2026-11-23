"""Unit tests for is800_2025.py (IS 800:2025 Draft)

Run from the folder that contains is800_2025.py (and Common.py, if you use the real one):

    pip install pytest
    python -m pytest test_is800_2025.py -v

Expected values are calculated by hand from the clauses of the draft (the arithmetic is written out in each test).
"""
import math

import pytest

from is800_2025 import IS800_2025 as IS


# ------------------------------------------------------------------
# Section 10 - Table 2, Table 3
# ------------------------------------------------------------------
class TestTable2:
    def test_section_class_names(self):
        assert IS._section_class_number('Plastic') == 1
        assert IS._section_class_number('Class 2') == 2
        assert IS._section_class_number('Semi-compact') == 3
        assert IS._section_class_number(4) == 4
        with pytest.raises(ValueError):
            IS._section_class_number('unknown')

    def test_stress_ratios_note_5(self):
        r_1, r_2 = IS.Table2_stress_ratios(300, 600, -50, 200)
        assert r_1 == pytest.approx(0.5)
        assert r_2 == pytest.approx(-0.25)

    def test_outstand_uniform(self):  # fy = 250 -> epsilon = 1
        assert IS.Table2_i_outstand(8.7, 1, 250, 'Plastic') == 'Pass'
        assert IS.Table2_i_outstand(8.8, 1, 250, 'Plastic') == 'Fail'
        assert IS.Table2_i_outstand(9.7, 1, 250, 'Compact') == 'Pass'
        assert IS.Table2_i_outstand(13.6, 1, 250, 'Semi-compact') == 'Pass'
        assert IS.Table2_i_outstand(13.7, 1, 250, 'Semi-compact') == 'Fail'

    def test_outstand_epsilon_for_fy_350(self):
        epsilon = math.sqrt(250 / 350)
        assert IS.Table2_i_outstand(8.7 * epsilon * 0.99, 1, 350, 'Plastic') == 'Pass'
        assert IS.Table2_i_outstand(8.7 * epsilon * 1.01, 1, 350, 'Plastic') == 'Fail'

    def test_outstand_non_uniform(self):
        # tip in compression, r1 = 0.5: limit = 8.7 / 0.5 = 17.4
        assert IS.Table2_i_outstand(17, 1, 250, 'Plastic', 'Non uniform', r_1=0.5, tip='compression') == 'Pass'
        assert IS.Table2_i_outstand(17.5, 1, 250, 'Plastic', 'Non uniform', r_1=0.5, tip='compression') == 'Fail'
        # tip in tension, r1 = 0.5: limit = 8.7 / (0.5 * sqrt(0.5)) = 24.6
        assert IS.Table2_i_outstand(24.5, 1, 250, 'Plastic', 'Non uniform', r_1=0.5, tip='tension') == 'Pass'
        assert IS.Table2_i_outstand(24.7, 1, 250, 'Plastic', 'Non uniform', r_1=0.5, tip='tension') == 'Fail'
        # the draft gives no Class 3 limit for non uniform stress
        assert IS.Table2_i_outstand(10, 1, 250, 'Semi-compact', 'Non uniform', r_1=0.5) == 'Not applicable'

    def test_web_axial_compression(self):
        assert IS.Table2_ii_web(32, 1, 250, 'Plastic', 'Axial compression') == 'Pass'
        assert IS.Table2_ii_web(33, 1, 250, 'Plastic', 'Axial compression') == 'Fail'
        assert IS.Table2_ii_web(36.8, 1, 250, 'Compact', 'Axial compression') == 'Pass'
        assert IS.Table2_ii_web(40.7, 1, 250, 'Semi-compact', 'Axial compression') == 'Pass'
        assert IS.Table2_ii_web(41, 1, 250, 'Semi-compact', 'Axial compression') == 'Fail'

    def test_web_neutral_axis_at_mid_depth(self):
        assert IS.Table2_ii_web(70, 1, 250, 'Plastic') == 'Pass'
        assert IS.Table2_ii_web(71, 1, 250, 'Plastic') == 'Fail'
        assert IS.Table2_ii_web(80, 1, 250, 'Compact') == 'Pass'
        assert IS.Table2_ii_web(120, 1, 250, 'Semi-compact') == 'Pass'
        assert IS.Table2_ii_web(121, 1, 250, 'Semi-compact') == 'Fail'

    def test_web_non_uniform_class_1_2(self):
        # r1 = 0.8 > 0.5 : 384 / (13*0.8 - 1) = 40.85
        assert IS.Table2_ii_web(40, 1, 250, 'Plastic', 'Non uniform', r_1=0.8) == 'Pass'
        assert IS.Table2_ii_web(41, 1, 250, 'Plastic', 'Non uniform', r_1=0.8) == 'Fail'
        # r1 = 0.4 <= 0.5 : 35 / 0.4 = 87.5
        assert IS.Table2_ii_web(87, 1, 250, 'Plastic', 'Non uniform', r_1=0.4) == 'Pass'
        assert IS.Table2_ii_web(88, 1, 250, 'Plastic', 'Non uniform', r_1=0.4) == 'Fail'
        # Class 2, r1 = 0.4 : 40.2 / 0.4 = 100.5
        assert IS.Table2_ii_web(100, 1, 250, 'Compact', 'Non uniform', r_1=0.4) == 'Pass'
        assert IS.Table2_ii_web(101, 1, 250, 'Compact', 'Non uniform', r_1=0.4) == 'Fail'

    def test_web_non_uniform_class_3(self):
        # r2 = 0 : 40.7 / 0.67 = 60.75
        assert IS.Table2_ii_web(60, 1, 250, 'Semi-compact', 'Non uniform', r_2=0) == 'Pass'
        assert IS.Table2_ii_web(61, 1, 250, 'Semi-compact', 'Non uniform', r_2=0) == 'Fail'
        # r2 = -1 : 60 * 2 * 1 = 120 (and 40.7 / 0.34 = 119.7 from the other branch: continuous)
        assert IS.Table2_ii_web(120, 1, 250, 'Semi-compact', 'Non uniform', r_2=-1) == 'Pass'
        assert IS.Table2_ii_web(121, 1, 250, 'Semi-compact', 'Non uniform', r_2=-1) == 'Fail'

    def test_web_non_uniform_requires_ratios(self):
        with pytest.raises(ValueError):
            IS.Table2_ii_web(50, 1, 250, 'Plastic', 'Non uniform')
        with pytest.raises(ValueError):
            IS.Table2_ii_web(50, 1, 250, 'Semi-compact', 'Non uniform')

    def test_angle_in_bending(self):
        assert IS.Table2_iii_angle_bending(8.7, 8.7, 1, 250, 'Plastic') == 'Pass'
        assert IS.Table2_iii_angle_bending(8.7, 8.8, 1, 250, 'Plastic') == 'Fail'  # both criteria needed
        assert IS.Table2_iii_angle_bending(14.5, 14.5, 1, 250, 'Semi-compact') == 'Pass'

    def test_angle_axial(self):
        assert IS.Table2_iv_angle_axial(11.1, 11.1, 1, 250) == 'Pass'  # (b+d)/t = 22.2 <= 22.3
        assert IS.Table2_iv_angle_axial(11.2, 11.2, 1, 250) == 'Fail'  # (b+d)/t = 22.4 > 22.3
        assert IS.Table2_iv_angle_axial(10, 10, 1, 250, 'Plastic') == 'Not applicable'

    def test_angle_leg_in_contact(self):
        assert IS.Table2_v_angle_leg_in_contact(9.7, 1, 250, 'Compact') == 'Pass'
        assert IS.Table2_v_angle_leg_in_contact(9.8, 1, 250, 'Compact') == 'Fail'

    def test_circular_hollow_tube(self):
        assert IS.Table2_vi_circular_hollow_tube(47, 1, 250, 'Moment', 'Plastic') == 'Pass'
        assert IS.Table2_vi_circular_hollow_tube(48, 1, 250, 'Moment', 'Plastic') == 'Fail'
        assert IS.Table2_vi_circular_hollow_tube(66, 1, 250, 'Moment', 'Compact') == 'Pass'
        assert IS.Table2_vi_circular_hollow_tube(85, 1, 250, 'Moment', 'Semi-compact') == 'Pass'
        assert IS.Table2_vi_circular_hollow_tube(86, 1, 250, 'Axial compression', 'Semi-compact') == 'Pass'
        assert IS.Table2_vi_circular_hollow_tube(87, 1, 250, 'Axial compression', 'Semi-compact') == 'Fail'
        assert IS.Table2_vi_circular_hollow_tube(50, 1, 250, 'Axial compression', 'Plastic') == 'Not applicable'
        # fy = 355 : epsilon^2 = 250/355 = 0.7042 -> 47 * 0.7042 = 33.10
        assert IS.Table2_vi_circular_hollow_tube(33.0, 1, 355, 'Moment', 'Plastic') == 'Pass'
        assert IS.Table2_vi_circular_hollow_tube(33.2, 1, 355, 'Moment', 'Plastic') == 'Fail'


class TestSlenderness:
    @pytest.mark.parametrize("row, limit", [(1, 180), (2, 180), (3, 250), (4, 300), (5, 350), (6, 400)])
    def test_table_3(self, row, limit):
        assert IS.cl_10_9_max_slenderness_ratio(row) == limit

    def test_invalid_type(self):
        with pytest.raises(ValueError):
            IS.cl_10_9_max_slenderness_ratio(7)


# ------------------------------------------------------------------
# Section 12 - Table 5
# ------------------------------------------------------------------
def test_table_5_values():
    t5 = IS.cl_12_4_1_Table_5
    assert t5['gamma_m0']['yielding'] == 1.10
    assert t5['gamma_m0']['buckling'] == 1.10
    assert t5['gamma_m1']['ultimate_stress'] == 1.25
    from is800_2025 import KEY_DP_FAB_SHOP, KEY_DP_FAB_FIELD
    assert t5['gamma_mb'][KEY_DP_FAB_SHOP] == 1.25
    assert t5['gamma_mf'][KEY_DP_FAB_FIELD] == 1.25
    assert t5['gamma_mw'][KEY_DP_FAB_SHOP] == 1.25
    assert t5['gamma_mw'][KEY_DP_FAB_FIELD] == 1.50


# ------------------------------------------------------------------
# Section 13 - Tension members
# ------------------------------------------------------------------
class TestTension:
    def test_yielding(self):
        # 1000 * 250 / 1.10
        assert IS.cl_13_2_tension_yielding_strength(1000, 250) == pytest.approx(227272.727, rel=1e-6)

    def test_rupture(self):
        # 0.9 * 800 * 410 / 1.25
        assert IS.cl_13_3_1_tension_rupture_strength(800, 410) == pytest.approx(236160.0)

    def test_threaded_rod(self):
        assert IS.cl_13_3_2_threaded_rod_rupture_strength(300, 400) == pytest.approx(0.9 * 300 * 400 / 1.25)

    def test_net_area_plate(self):
        # (100 - 2*18) * 10
        assert IS.cl_13_3_1_net_effective_area_plate(100, 10, 2, 18) == pytest.approx(640.0)
        # punched holes: dh = 18 + 2 -> (100 - 2*20) * 10
        assert IS.cl_13_3_1_net_effective_area_plate(100, 10, 2, 18, punched=True) == pytest.approx(600.0)
        # one inclined leg, ps = 50, g = 40 : 50^2 / (4*40) = 15.625
        assert IS.cl_13_3_1_net_effective_area_plate(100, 10, 2, 18, staggers=[(50, 40)]) == pytest.approx(
            (100 - 36 + 15.625) * 10)

    def test_beta_single_angle(self):
        # 1.4 - 0.076 * (50/6) * (250/410) * (40/100) = 1.2455 ; upper bound 0.9*410*1.1/(250*1.25) = 1.2989
        beta = IS.cl_13_3_3_shear_lag_factor_beta(50, 6, 40, 100, 250, 410)
        assert beta == pytest.approx(1.4 - 0.076 * (50 / 6) * (250 / 410) * 0.4)
        assert beta == pytest.approx(1.2455, abs=1e-3)

    def test_beta_limits(self):
        # a very long shear lag width pushes beta below 0.7 -> lower limit 0.7
        assert IS.cl_13_3_3_shear_lag_factor_beta(100, 4, 100, 50, 250, 410) == pytest.approx(0.7)
        # a very short shear lag width pushes beta above the upper bound
        upper = 0.9 * 410 * 1.1 / (250 * 1.25)
        assert IS.cl_13_3_3_shear_lag_factor_beta(10, 10, 1, 1000, 250, 410) == pytest.approx(min(1.4, upper))

    def test_single_angle_rupture(self):
        beta = 1.4 - 0.076 * (50 / 6) * (250 / 410) * 0.4
        expected = 0.9 * 400 * 410 / 1.25 + beta * 300 * 250 / 1.1
        assert IS.cl_13_3_3_single_angle_rupture_strength(400, 300, 50, 6, 40, 100, 250, 410) == pytest.approx(expected)

    def test_block_shear(self):
        A_vg, A_vn, A_tg, A_tn, f_u, f_y = 1200, 900, 500, 400, 410, 250
        t1 = A_vg * f_y / (math.sqrt(3) * 1.1) + 0.9 * A_tn * f_u / 1.25
        t2 = 0.9 * A_vn * f_u / (math.sqrt(3) * 1.25) + A_tg * f_y / 1.1
        assert IS.cl_13_4_1_block_shear_strength(A_vg, A_vn, A_tg, A_tn, f_u, f_y) == pytest.approx(min(t1, t2))
        # hand values: T_db1 = 275 539 N, T_db2 = 267 027 N -> the second expression governs
        assert t1 == pytest.approx(275539.2, rel=1e-5)
        assert t2 == pytest.approx(267026.8, rel=1e-5)
        assert IS.cl_13_4_1_block_shear_strength(A_vg, A_vn, A_tg, A_tn, f_u, f_y) == pytest.approx(267026.8, rel=1e-5)


# ------------------------------------------------------------------
# Section 14 - Compression members
# ------------------------------------------------------------------
class TestCompression:
    @pytest.mark.parametrize("cls, alpha", [('a0', 0.13), ('a', 0.21), ('b', 0.34), ('c', 0.49), ('d', 0.76)])
    def test_table_7(self, cls, alpha):
        assert IS.cl_14_1_2_3_imperfection_factor(cls) == alpha

    def test_table_7_invalid_class(self):
        with pytest.raises(KeyError):
            IS.cl_14_1_2_3_imperfection_factor('e')

    def test_design_compressive_stress_class_b_kl_r_100(self):
        # lambda = sqrt(250 / (pi^2 * 2e5 / 100^2)) = 1.1254
        # phi = 0.5 (1 + 0.34 (1.1254 - 0.2) + 1.1254^2) = 1.2906
        # chi = 1 / (1.2906 + sqrt(1.2906^2 - 1.1254^2)) = 0.5202 ; f_cd = 250 * 0.5202 / 1.1 = 118.2 MPa
        result = IS.cl_14_1_2_1_design_compressive_stress(250, 1.1, 100, 0.34, 2e5, 'Concentric')
        assert result[1] == pytest.approx(1.1254, abs=1e-3)
        assert result[2] == pytest.approx(1.2906, abs=1e-3)
        assert result[3] == pytest.approx(0.5202, abs=1e-3)
        assert result[5] == pytest.approx(118.2, abs=0.2)

    def test_design_compressive_stress_is_limited_by_fy_gamma(self):
        # very stocky column: chi is 1.0 and f_cd cannot exceed fy / gamma_m0
        result = IS.cl_14_1_2_1_design_compressive_stress(250, 1.1, 10, 0.21, 2e5, 'Concentric')
        assert result[5] == pytest.approx(250 / 1.1)

    def test_design_compressive_stress_leg_check_type(self):
        result = IS.cl_14_1_2_1_design_compressive_stress(250, 1.1, 100, 0.49, 2e5, ('Leg', 1.0))
        assert result[1] == 1.0

    def test_design_compressive_stress_invalid_check_type(self):
        with pytest.raises(ValueError):
            IS.cl_14_1_2_1_design_compressive_stress(250, 1.1, 100, 0.34, 2e5, 'other')

    def test_member_check(self):
        assert IS.cl_14_1_2_design_compressive_strength_member(1000, 100, 90000) == 'pass'
        assert IS.cl_14_1_2_design_compressive_strength_member(1000, 100, 100000) == 'fail'

    # ---- Table 10 ----
    def test_rolled_i_fy_250(self):
        assert IS.cl_14_1_2_3_buckling_class_of_crosssections(150, 300, 20, 250) == {'z-z': 'a', 'y-y': 'b'}
        assert IS.cl_14_1_2_3_buckling_class_of_crosssections(150, 300, 60, 250) == {'z-z': 'b', 'y-y': 'c'}
        assert IS.cl_14_1_2_3_buckling_class_of_crosssections(250, 280, 20, 250) == {'z-z': 'b', 'y-y': 'c'}
        assert IS.cl_14_1_2_3_buckling_class_of_crosssections(250, 280, 120, 250) == {'z-z': 'd', 'y-y': 'd'}

    def test_rolled_i_fy_above_420(self):
        # high strength column (5) of Table 10
        assert IS.cl_14_1_2_3_buckling_class_of_crosssections(150, 300, 20, 460) == {'z-z': 'a0', 'y-y': 'a'}
        assert IS.cl_14_1_2_3_buckling_class_of_crosssections(150, 300, 60, 460) == {'z-z': 'a', 'y-y': 'b'}
        assert IS.cl_14_1_2_3_buckling_class_of_crosssections(250, 280, 20, 460) == {'z-z': 'a', 'y-y': 'b'}
        assert IS.cl_14_1_2_3_buckling_class_of_crosssections(250, 280, 120, 460) == {'z-z': 'c', 'y-y': 'c'}

    def test_fy_boundary_420(self):
        assert IS.cl_14_1_2_3_buckling_class_of_crosssections(150, 300, 20, 420)['z-z'] == 'a'
        assert IS.cl_14_1_2_3_buckling_class_of_crosssections(150, 300, 20, 421)['z-z'] == 'a0'

    def test_welded_i(self):
        assert IS.cl_14_1_2_3_buckling_class_of_crosssections(200, 400, 30, 250, 'Welded I-section') == \
               {'z-z': 'b', 'y-y': 'c'}
        assert IS.cl_14_1_2_3_buckling_class_of_crosssections(200, 400, 50, 250, 'Welded I-section') == \
               {'z-z': 'c', 'y-y': 'd'}
        assert IS.cl_14_1_2_3_buckling_class_of_crosssections(200, 400, 30, 460, 'Welded I-section') == \
               {'z-z': 'b', 'y-y': 'c'}

    def test_hollow_sections(self):
        hot = 'Hot rolled'
        cold = 'Cold formed'
        assert IS.cl_14_1_2_3_buckling_class_of_crosssections(0, 0, 0, 250, 'Hollow Section', hot) == \
               {'z-z': 'a', 'y-y': 'a'}
        assert IS.cl_14_1_2_3_buckling_class_of_crosssections(0, 0, 0, 460, 'Hollow Section', hot) == \
               {'z-z': 'a0', 'y-y': 'a0'}
        assert IS.cl_14_1_2_3_buckling_class_of_crosssections(0, 0, 0, 250, 'Hollow Section', cold) == \
               {'z-z': 'b', 'y-y': 'b'}
        assert IS.cl_14_1_2_3_buckling_class_of_crosssections(0, 0, 0, 460, 'Hollow Section', cold) == \
               {'z-z': 'c', 'y-y': 'c'}

    def test_other_rows(self):
        f = IS.cl_14_1_2_3_buckling_class_of_crosssections
        assert f(0, 0, 0, 250, 'Welded Box Section, Cruciform') == {'z-z': 'b', 'y-y': 'b'}
        assert f(0, 0, 0, 250, 'Welded Box Section, Cruciform', thick_welds=True, b_by_t_f=25, h_by_t_w=40) == \
               {'z-z': 'c', 'y-y': 'b'}
        assert f(0, 0, 0, 460, 'Channel, Angle, T and Solid Sections') == {'z-z': 'c', 'y-y': 'c'}
        assert f(0, 0, 0, 250, 'Built-up Member (Rolled Sections)') == {'z-z': 'b', 'y-y': 'b'}
        assert f(0, 0, 0, 460, 'Built-up Member (Rolled Sections)') == {'z-z': 'a', 'y-y': 'a'}
        assert f(0, 0, 0, 250, 'Built-up Member (Welded Sections)') == {'z-z': 'c', 'y-y': 'c'}

    def test_unknown_cross_section(self):
        with pytest.raises(ValueError):
            IS.cl_14_1_2_3_buckling_class_of_crosssections(0, 0, 0, 250, 'Tube')

    # ---- column base ----
    def test_bearing_strength_without_areas_is_0_45_fck(self):
        assert IS.cl_14_4_1_bearing_strength_concrete('M25') == pytest.approx(11.25)

    def test_bearing_strength_with_areas(self):
        # A1/A2 = 1.44 -> sqrt = 1.2 -> 0.45 * 25 * 1.2 = 13.5
        assert IS.cl_14_4_1_bearing_strength_concrete('M25', 1440, 1000) == pytest.approx(13.5)

    def test_bearing_strength_capped_at_0_9_fck(self):
        # A1/A2 = 9 -> 0.45 * 25 * 3 = 33.75 > 0.9 * 25 = 22.5
        assert IS.cl_14_4_1_bearing_strength_concrete('M25', 9000, 1000) == pytest.approx(22.5)

    def test_bearing_strength_invalid(self):
        with pytest.raises(KeyError):
            IS.cl_14_4_1_bearing_strength_concrete('M99')
        with pytest.raises(ValueError):
            IS.cl_14_4_1_bearing_strength_concrete('M25', 100, 0)


# ------------------------------------------------------------------
# Section 15 - Lateral torsional buckling
# ------------------------------------------------------------------
class TestLateralTorsionalBuckling:
    def test_alpha_LT_rolled(self):
        f = IS.cl_15_2_2_imperfection_parameter_alpha_LT
        # h/b = 2 > 1.2, tf = 20 <= 40 : 0.12 * sqrt(4) = 0.24
        assert f('Rolled I or H', h=300, b=150, t_f=20, Z_ez=4.0, Z_ey=1.0) == pytest.approx(0.24)
        # capped at 0.34 : 0.12 * sqrt(9) = 0.36
        assert f('Rolled I or H', h=300, b=150, t_f=20, Z_ez=9.0, Z_ey=1.0) == pytest.approx(0.34)
        # tf = 50 > 40 : 0.16 * sqrt(4) = 0.32 ; capped at 0.49 : 0.16 * sqrt(16) = 0.64
        assert f('Rolled I or H', h=300, b=150, t_f=50, Z_ez=4.0, Z_ey=1.0) == pytest.approx(0.32)
        assert f('Rolled I or H', h=300, b=150, t_f=50, Z_ez=16.0, Z_ey=1.0) == pytest.approx(0.49)
        # h/b <= 1.2 (third row): 0.12 sqrt(Zez/Zey)
        assert f('Rolled I or H', h=200, b=200, t_f=50, Z_ez=4.0, Z_ey=1.0) == pytest.approx(0.24)

    def test_alpha_LT_welded_and_others(self):
        f = IS.cl_15_2_2_imperfection_parameter_alpha_LT
        assert f('Welded I', h=500, b=200, t_f=20, Z_ez=4.0, Z_ey=1.0) == pytest.approx(0.24)
        assert f('Welded I', h=500, b=200, t_f=50, Z_ez=16.0, Z_ey=1.0) == pytest.approx(0.34)
        assert f('Rolled unequal I or H', h=300, b=150) == 0.21     # h/bmin = 2.0
        assert f('Rolled unequal I or H', h=330, b=150) == 0.34     # h/bmin = 2.2
        assert f('Welded unequal I', h=300, b=150) == 0.49
        assert f('Welded unequal I', h=330, b=150) == 0.76
        assert f('Other rolled') == 0.76

    def test_alpha_LT_errors(self):
        with pytest.raises(ValueError):
            IS.cl_15_2_2_imperfection_parameter_alpha_LT('Rolled I or H', h=300, b=150, t_f=20)
        with pytest.raises(ValueError):
            IS.cl_15_2_2_imperfection_parameter_alpha_LT('Tube')

    def test_f_M_table_14(self):
        f = IS.cl_15_2_2_moment_gradient_factor_f_M
        assert f('uniform moment') == 1.0
        assert f('linear moment', psi=0) == pytest.approx(1.25)
        assert f('linear moment', psi=1) == pytest.approx(1.0)       # 1.25 - 0.1 - 0.15
        assert f('linear moment', psi=-1) == pytest.approx(1.2)      # 1.25 + 0.1 - 0.15
        assert f('udl') == 1.05
        assert f('central point load') == 1.10
        assert f('udl with equal end moments', M0_by_Mh=0) == pytest.approx(1.0)
        assert f('udl with equal end moments', M0_by_Mh=1) == pytest.approx(1.0 + 1.35 - 0.33)
        assert f('udl with equal end moments', M0_by_Mh=2) == 1.05
        assert f('udl with one end moment', M0_by_Mh=1) == pytest.approx(1.25 + 0.5 - 0.275)
        assert f('udl with one end moment', M0_by_Mh=1.47) == 1.05
        assert f('point load with equal end moments', M0_by_Mh=1) == pytest.approx(1.0 + 1.25 - 0.30)
        assert f('point load with equal end moments', M0_by_Mh=3) == 1.10
        assert f('point load with one end moment', M0_by_Mh=1) == pytest.approx(1.25 + 0.325 - 0.175)
        assert f('point load with one end moment', M0_by_Mh=1.5) == 1.10

    def test_f_M_is_continuous_at_the_breakpoints(self):
        f = IS.cl_15_2_2_moment_gradient_factor_f_M
        # polynomial value just below the break point is within 0.02 of the constant above it
        assert f('udl with equal end moments', M0_by_Mh=1.9999) == pytest.approx(1.05, abs=0.02)
        assert f('udl with one end moment', M0_by_Mh=1.4699) == pytest.approx(1.05, abs=0.02)
        assert f('point load with equal end moments', M0_by_Mh=1.9999) == pytest.approx(1.10, abs=0.02)
        assert f('point load with one end moment', M0_by_Mh=1.4999) == pytest.approx(1.10, abs=0.02)

    def test_f_M_errors(self):
        f = IS.cl_15_2_2_moment_gradient_factor_f_M
        with pytest.raises(ValueError):
            f('linear moment')
        with pytest.raises(ValueError):
            f('linear moment', psi=2)
        with pytest.raises(ValueError):
            f('udl with equal end moments')
        with pytest.raises(ValueError):
            f('something else')

    def test_beta_b(self):
        f = IS.cl_15_2_2_beta_b
        assert f('Plastic', 1000) == 1.0
        assert f('Compact', 1000) == 1.0
        assert f('Semi-compact', 1000, Z_e=900) == pytest.approx(0.9)
        assert f('Slender', 1000, Z_eff=800) == pytest.approx(0.8)

    def test_elastic_buckling_moment(self):
        E, mu, I_y, I_t, I_w, L = 2e5, 0.3, 1e7, 1e5, 1e11, 4000
        G = 2e5 / 2.6
        term_1 = math.pi ** 2 * E * I_y / L ** 2          # 1 233 700.5
        term_2 = G * I_t + math.pi ** 2 * E * I_w / L ** 2
        expected = math.sqrt(term_1 * term_2)
        assert IS.cl_15_2_2_elastic_buckling_moment(E, mu, I_y, I_t, I_w, L) == pytest.approx(expected)
        assert expected == pytest.approx(1.572e8, rel=1e-3)

    def test_fcr_b_approx(self):
        # L/ry = 100, hf/tf = 30 : 1.1 pi^2 2e5 / 1e4 * sqrt(1 + (100/30)^2 / 20) = 217.1 * 1.2469
        expected = 1.1 * math.pi ** 2 * 2e5 / 100 ** 2 * math.sqrt(1 + (100 / 30) ** 2 / 20)
        assert IS.cl_15_2_2_1_fcr_b_approx(2e5, 100, 30) == pytest.approx(expected)
        assert expected == pytest.approx(270.7, abs=0.5)

    def test_fcr_b_decreases_with_slenderness(self):
        a = IS.cl_15_2_2_1_fcr_b_approx(2e5, 60, 30)
        b = IS.cl_15_2_2_1_fcr_b_approx(2e5, 120, 30)
        assert a > b

    def test_lambda_LT(self):
        # beta_b Zp fy / Mcr = 1 * 1e6 * 250 / 2.5e8 = 1.0 -> 1.0 ; 1.2 Ze fy / Mcr = 1.2*9e5*250/2.5e8 = 1.08 -> 1.0392
        assert IS.cl_15_2_2_non_dimensional_slenderness_lambda_LT(1.0, 1e6, 9e5, 250, 2.5e8) == pytest.approx(1.0)
        # the second limit governs when Ze is small: 1.2 * 5e5 * 250 / 2.5e8 = 0.6 -> 0.7746 < 1.0
        assert IS.cl_15_2_2_non_dimensional_slenderness_lambda_LT(1.0, 1e6, 5e5, 250, 2.5e8) == pytest.approx(
            math.sqrt(0.6))

    def test_lambda_y(self):
        # L/ry = 100 -> fcry = 197.39 MPa -> sqrt(250 / 197.39) = 1.1254
        assert IS.cl_15_2_2_non_dimensional_slenderness_lambda_y(250, 2e5, 5000, 50) == pytest.approx(1.1254, abs=1e-3)

    def test_phi_LT(self):
        # fM = 1, alpha = 0.21, lambda_LT = 0.8, lambda_y = 0.6 :
        # 0.5 [1 + (0.8/0.6)^2 * 0.21 * 0.6 + 0.64] = 0.5 [1 + 0.224 + 0.64] = 0.932
        assert IS.cl_15_2_2_phi_LT(0.21, 0.8, 0.6, 1.0) == pytest.approx(0.932)

    def test_phi_LT_reduces_to_2007_form_when_fM_1_and_lambda_equal(self):
        # if lambda_LT = lambda_y and f_M = 1, the 2025 phi_LT equals the 2007 phi_LT
        lam, alpha = 0.9, 0.34
        assert IS.cl_15_2_2_phi_LT(alpha, lam, lam, 1.0) == pytest.approx(0.5 * (1 + alpha * (lam - 0.2) + lam ** 2))

    def test_chi_LT(self):
        phi = 0.932
        expected = 1.0 / (phi + math.sqrt(phi ** 2 - 0.8 ** 2))
        assert IS.cl_15_2_2_chi_LT(phi, 0.8, 1.0) == pytest.approx(expected)
        assert expected == pytest.approx(0.7092, abs=1e-3)

    def test_chi_LT_with_moment_gradient(self):
        phi, lam, fm = 0.9, 0.7, 1.25
        expected = fm / (phi + math.sqrt(phi ** 2 - fm * lam ** 2))
        assert IS.cl_15_2_2_chi_LT(phi, lam, fm) == pytest.approx(min(expected, 1.0))

    def test_chi_LT_never_exceeds_one(self):
        # a small lambda with f_M = 1.25 gives a value above 1 before the limit is applied
        assert IS.cl_15_2_2_chi_LT(0.52, 0.1, 1.25) == 1.0

    def test_check_not_needed(self):
        f = IS.cl_15_2_2_lateral_torsional_buckling_check_not_needed
        assert f(0.3) is True
        assert f(0.5) is False
        assert f(0.5, bending_axis='minor') is True
        assert f(0.5, hollow_or_solid=True) is True

    def test_design_bending_strength(self):
        f_bd = IS.cl_15_2_2_design_bending_compressive_stress(0.7, 250)
        assert f_bd == pytest.approx(0.7 * 250 / 1.1)
        assert IS.cl_15_2_2_design_bending_strength(1.0, 1e6, f_bd) == pytest.approx(1e6 * 0.7 * 250 / 1.1)
        assert IS.cl_15_2_2_design_bending_compressive_stress(0.7, 250, 1.0) == pytest.approx(175.0)


# ------------------------------------------------------------------
# Section 17 - Connections
# ------------------------------------------------------------------
class TestBoltGeometry:
    @pytest.mark.parametrize("d, hole_type, size", [
        (10, 'Standard', 10),
        (12, 'Standard', 13),
        (16, 'Standard', 18),
        (20, 'Standard', 22),
        (24, 'Standard', 26),
        (30, 'Standard', 33),
        (20, 'Over-sized', 24),
        (24, 'Over-sized', 30),
        (30, 'Over-sized', 38),
        (20, 'short_slot', 26),
        (30, 'short_slot', 40),
        (20, 'long_slot', 70),   # (2.5 + 1) * 20
    ])
    def test_table_19(self, d, hole_type, size):
        assert IS.cl_17_2_1_bolt_hole_size(d, hole_type) == size

    def test_min_spacing(self):
        assert IS.cl_17_2_2_min_spacing(20) == 50

    def test_max_spacing(self):
        assert IS.cl_17_2_3_1_max_spacing([10, 12]) == 300.0       # 32 * 10 = 320 -> 300
        assert IS.cl_17_2_3_1_max_spacing([8, 12]) == 256          # 32 * 8

    def test_max_pitch(self):
        f = IS.cl_17_2_3_2_max_pitch_tension_compression
        assert f(20, [10, 12], 'tension') == 160                   # 16 * 10
        assert f(20, [15], 'tension') == 200.0                     # 240 -> 200
        assert f(20, [10], 'compression') == 120                   # 12 * 10
        assert f(20, [20], 'compression') == 200.0
        assert f(20, [10], 'compression_butting') == 90            # 4.5 * 20
        with pytest.raises(ValueError):
            f(20, [10], 'other')

    def test_max_spacing_along_edge(self):
        assert IS.cl_17_2_3_3_max_spacing_along_edge([10, 12]) == 140.0    # 100 + 4 * 10
        assert IS.cl_17_2_3_3_max_spacing_along_edge([40]) == 200.0        # 260 -> 200

    def test_min_edge_distance(self):
        f = IS.cl_17_2_4_2_min_edge_end_dist
        assert f(20) == pytest.approx(1.7 * 22)
        assert f(20, edge_type='Rolled, machine flame cut, sawn or planed') == pytest.approx(1.5 * 22)
        assert f(20, 'Over-sized') == pytest.approx(1.7 * 24)

    def test_max_edge_distance(self):
        f = IS.cl_17_2_4_3_max_edge_dist
        assert f([(12, 410, 250)]) == pytest.approx(144.0)                     # 12 * 12 * 1
        assert f([(12, 410, 250)], corrosive_influences=True) == pytest.approx(88.0)   # 40 + 4 * 12
        # the plate with the smaller t * epsilon governs: 10 * sqrt(250/350) = 8.45 -> 101.4
        assert f([(12, 410, 250), (10, 490, 350)]) == pytest.approx(12 * 10 * math.sqrt(250 / 350))


class TestBearingBolts:
    def test_design_strength_is_the_smaller(self):
        assert IS.cl_17_3_2_bolt_design_strength(80000, 100000) == 80000
        assert IS.cl_17_3_2_bolt_design_strength(120000, 100000) == 100000

    def test_shear_capacity(self):
        # M20, 8.8: fub = 800, Anb = 245, one shear plane through threads
        expected = 800 / math.sqrt(3) * 245 / 1.25
        assert IS.cl_17_3_3_bolt_shear_capacity(800, 245, 314.16, 1) == pytest.approx(expected)
        assert expected == pytest.approx(90530, rel=1e-3)

    def test_shear_capacity_uses_both_areas(self):
        expected = 800 / math.sqrt(3) * (1 * 245 + 1 * 314.16) / 1.25
        assert IS.cl_17_3_3_bolt_shear_capacity(800, 245, 314.16, 1, 1) == pytest.approx(expected)

    def test_shear_capacity_uses_the_safety_factor_parameter(self):
        from is800_2025 import KEY_DP_FAB_FIELD
        a = IS.cl_17_3_3_bolt_shear_capacity(800, 245, 314.16, 1)
        b = IS.cl_17_3_3_bolt_shear_capacity(800, 245, 314.16, 1, safety_factor_parameter=KEY_DP_FAB_FIELD)
        assert a == pytest.approx(b)    # gamma_mb is 1.25 for both shop and field

    def test_long_joint(self):
        f = IS.cl_17_3_3_1_bolt_long_joint
        assert f(20, 200) == 1.0                          # 200 < 15 d = 300
        assert f(20, 400) == pytest.approx(0.975)         # 1.075 - 0.005 * 20
        assert f(20, 1000) == pytest.approx(0.825)
        assert f(20, 2000) == 0.75                        # 0.575 -> lower limit 0.75

    def test_large_grip(self):
        f = IS.cl_17_3_3_2_bolt_large_grip
        assert f(20, 100) == 1.0                          # lg = 5 d
        assert f(20, 140) == pytest.approx(0.8)           # 8 / (3 + 7)
        assert f(20, 160) == pytest.approx(0.73)          # 8 / 11 = 0.727
        assert f(20, 140, l_j=1000) == pytest.approx(0.8)  # beta_lj = 0.825 is not smaller
        assert f(20, 140, l_j=2000) == pytest.approx(0.75)  # beta_lj = 0.75 governs

    def test_grip_length_limit(self):
        assert IS.cl_17_3_3_2_grip_length_ok(20, 160) is True
        assert IS.cl_17_3_3_2_grip_length_ok(20, 161) is False

    def test_packing_plates(self):
        assert IS.cl_17_3_3_3_packing_plates(6) == 1.0
        assert IS.cl_17_3_3_3_packing_plates(10) == pytest.approx(0.875)

    def test_bearing_capacity_rounded_k_b(self):
        # d0 = 22, kb = min(40/66, 60/66 - 0.25, 800/410, 1) = 0.606 -> 0.61
        # V = 2.5 * 0.61 * 20 * 10 * 410 / 1.25 = 100 040 N
        assert IS.cl_17_3_4_bolt_bearing_capacity(410, 800, 10, 20, 40, 60) == pytest.approx(100040.0)

    def test_bearing_capacity_exact_k_b(self):
        expected = 2.5 * (40 / 66) * 20 * 10 * 410 / 1.25
        assert IS.cl_17_3_4_bolt_bearing_capacity(410, 800, 10, 20, 40, 60, round_k_b=False) == pytest.approx(expected)

    def test_bearing_capacity_without_pitch(self):
        # p = 0: kb = min(e / (3 d0), fub / fu, 1) = min(1.2, 1.95, 1) -> 1.0
        assert IS.cl_17_3_4_bolt_bearing_capacity(410, 800, 10, 20, 80, 0) == pytest.approx(
            2.5 * 1.0 * 20 * 10 * 410 / 1.25)

    def test_bearing_capacity_slotted_holes(self):
        # oversize hole d0 = 24 -> kb = min(40/72, 60/72 - 0.25, 1.95, 1) = 0.5556 -> 0.56 ; x 0.7
        expected = 2.5 * 0.56 * 20 * 10 * 410 / 1.25 * 0.7
        assert IS.cl_17_3_4_bolt_bearing_capacity(410, 800, 10, 20, 40, 60, 'Over-sized') == pytest.approx(expected)
        # long slot d0 = 70 -> kb = min(40/210, 60/210 - 0.25, ...) = 0.0357 -> 0.04 ; x 0.5
        expected = 2.5 * 0.04 * 20 * 10 * 410 / 1.25 * 0.5
        assert IS.cl_17_3_4_bolt_bearing_capacity(410, 800, 10, 20, 40, 60, 'long_slot') == pytest.approx(expected)

    def test_tension_resistance(self):
        # min(0.9 * 800 * 245, 640 * 314.16 * 1.25 / 1.1) = min(176 400, 228 480) ; / 1.25
        assert IS.cl_17_3_5_bearing_bolt_tension_resistance(800, 640, 314.16, 245) == pytest.approx(141120.0)

    def test_combined_shear_and_tension(self):
        assert IS.cl_17_3_6_bearing_bolt_combined_shear_and_tension(30, 60, 40, 80) == pytest.approx(0.5)
        assert IS.cl_17_3_6_bearing_bolt_combined_shear_and_tension(60, 60, 80, 80) == pytest.approx(2.0)


class TestFrictionGripBolts:
    def test_slip_resistance_ultimate(self):
        # F0 = 0.7 * 1000 * 245 = 171 500 ; V = 0.5 * 1 * 1.0 * 171 500 / 1.25 = 68 600
        V, K_h, gamma = IS.cl_17_4_3_bolt_slip_resistance(1000, 245, 1, 0.5)
        assert V == pytest.approx(68600.0)
        assert K_h == 1.0
        assert gamma == 1.25

    def test_slip_resistance_service(self):
        V, K_h, gamma = IS.cl_17_4_3_bolt_slip_resistance(1000, 245, 1, 0.5, slip_resistance='service_load')
        assert V == pytest.approx(0.5 * 171500 / 1.10)
        assert gamma == 1.10

    def test_slip_factor_is_limited_to_0_55(self):
        V, _, _ = IS.cl_17_4_3_bolt_slip_resistance(1000, 245, 1, 0.9)
        assert V == pytest.approx(0.55 * 171500 / 1.25)

    def test_hole_type_factor(self):
        f = IS.cl_17_4_3_bolt_slip_resistance
        assert f(1000, 245, 1, 0.5, 'Over-sized')[1] == 0.85
        assert f(1000, 245, 1, 0.5, 'short_slot')[1] == 0.85
        assert f(1000, 245, 1, 0.5, 'long_slot')[1] == 0.85
        assert f(1000, 245, 1, 0.5, 'long_slot_parallel')[1] == 0.7
        with pytest.raises(ValueError):
            f(1000, 245, 1, 0.5, 'unknown')

    def test_table_20(self):
        assert IS.cl_17_4_3_Table_20 == [0.20, 0.50, 0.10, 0.25, 0.30, 0.52, 0.30, 0.30, 0.50, 0.33, 0.48, 0.1]

    def test_tension_resistance(self):
        # min(0.9 * 1000 * 245, 900 * 314.16 * 1.25/1.1) = 220 500 ; / 1.25
        assert IS.cl_17_4_5_friction_bolt_tension_resistance(1000, 900, 314.16, 245) == pytest.approx(176400.0)

    def test_combined_shear_and_tension(self):
        assert IS.cl_17_4_6_friction_bolt_combined_shear_and_tension(30, 60, 40, 80) == pytest.approx(0.5)

    def test_prying_force(self):
        # beta = 2, f_o = 560, f_y = 250, t = 20 -> 1.1 * 20 * sqrt(2 * 560 / 250) = 46.57 ; end distance 40 governs
        T_e, l_v, f_o, b_e, t, f_y, end = 50000, 40, 560, 100, 20, 250, 40
        l_e = min(end, 1.1 * t * math.sqrt(2 * f_o / f_y))
        expected = (l_v / (2 * l_e)) * (T_e - 2 * 1.5 * f_o * b_e * t ** 4 / (27 * l_e * l_v ** 2))
        result = IS.cl_17_4_7_bolt_prying_force(T_e, l_v, f_o, b_e, t, f_y, end)
        assert l_e == 40
        assert result == pytest.approx(max(expected, 0), abs=0.01)

    def test_prying_force_is_not_negative(self):
        assert IS.cl_17_4_7_bolt_prying_force(100, 40, 560, 100, 20, 250, 40) == 0.0

    def test_prying_pretensioned_uses_beta_1(self):
        a = IS.cl_17_4_7_bolt_prying_force(60000, 40, 560, 100, 12, 250, 40, 'Pre-tensioned')
        b = IS.cl_17_4_7_bolt_prying_force(60000, 40, 560, 100, 12, 250, 40, '')
        assert a != b


class TestWelds:
    def test_min_weld_size_table_21(self):
        f = IS.cl_17_5_2_3_min_weld_size
        assert f(8, 10) == 3
        assert f(12, 20) == 5
        assert f(25, 30) == 6
        assert f(40, 45) == 10
        assert f(40, 8) == 8       # Note 1: not more than the thinner part

    def test_max_throat(self):
        assert IS.cl_17_5_3_1_max_weld_throat_thickness(10, 12) == pytest.approx(7.0)
        assert IS.cl_17_5_3_1_max_weld_throat_thickness(10, 12, special_circumstance=True) == 10

    @pytest.mark.parametrize("angle, K", [(60, 0.70), (90, 0.70), (91, 0.65), (100, 0.65), (101, 0.60), (106, 0.60),
                                          (107, 0.55), (113, 0.55), (114, 0.50), (120, 0.50)])
    def test_table_22(self, angle, K):
        assert IS.cl_17_5_3_2_factor_for_throat_thickness(angle) == K
        assert IS.cl_17_5_3_2_fillet_weld_effective_throat_thickness_constant(angle) == K

    def test_table_22_outside_range(self):
        assert IS.cl_17_5_3_2_factor_for_throat_thickness(45) is None
        assert IS.cl_17_5_3_2_factor_for_throat_thickness(130) is None

    def test_effective_throat(self):
        assert IS.cl_17_5_3_2_fillet_weld_effective_throat_thickness(6, 90) == pytest.approx(4.2)
        assert IS.cl_17_5_3_2_fillet_weld_effective_throat_thickness(3, 90) == 3    # not less than 3 mm
        assert IS.cl_17_5_3_2_fillet_weld_effective_throat_thickness(10, 110) == pytest.approx(5.5)

    def test_groove_weld(self):
        assert IS.cl_17_5_3_3_groove_weld_effective_throat_thickness(12, 16) == 12

    def test_effective_length(self):
        assert IS.cl_17_5_4_1_fillet_weld_effective_length(6, 24) == 0         # not more than 4 x size
        assert IS.cl_17_5_4_1_fillet_weld_effective_length(6, 100) == 88       # 100 - 2 * 6

    def test_design_stress(self):
        from is800_2025 import KEY_DP_FAB_SHOP, KEY_DP_FAB_FIELD
        shop = IS.cl_17_5_7_1_1_fillet_weld_design_stress([410, 440], KEY_DP_FAB_SHOP)
        field = IS.cl_17_5_7_1_1_fillet_weld_design_stress([410, 440], KEY_DP_FAB_FIELD)
        assert shop == pytest.approx(410 / math.sqrt(3) / 1.25)      # 189.4 MPa
        assert field == pytest.approx(410 / math.sqrt(3) / 1.50)     # 157.8 MPa

    def test_long_joint(self):
        f = IS.cl_17_5_7_3_weld_long_joint
        assert f(100, 5) == 1.0
        assert f(750, 5) == 1.0                                    # l_j = 150 t_t
        assert f(1500, 5) == pytest.approx(0.8)                    # 1.2 - 0.2 * 2
        assert f(3000, 5) == pytest.approx(0.4)                    # no lower limit in the draft
        assert f(3000, 5, lower_bound=0.6) == pytest.approx(0.6)   # the 2007 Osdag behaviour
