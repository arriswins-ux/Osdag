"""Module for Indian Standard, IS 800 : 2025 (Draft Revision, Doc: CED 07 (27869) WC, April 2025)

Companion of ``is800_2007.py``. Functions keep the signature style of the 2007 module
(``@staticmethod`` inside one class, clause number in the function name, "Reference" in the docstring),
but the clause numbers follow the 2025 draft.

Main differences from IS 800:2007 that are implemented here
-----------------------------------------------------------
* Clause renumbering: Section 1 sub-clauses became Clauses 1-8, so most main sections shift
  upward by 7 (Sec. 5 -> 12, Sec. 6 -> 13, Sec. 7 -> 14, Sec. 8 -> 15, Sec. 10 -> 17, cl. 3.7 -> 10.8, cl. 3.8 -> 10.9).
  Section 11 (Working Stress Design) of 2007 was removed.
* Table 2 (cl. 10.8): limiting width-to-thickness ratios changed, r1 / r2 redefined.
* Table 7 (cl. 14.1.2.3): new imperfection factor class a0 = 0.13.
* Table 10 (cl. 14.1.2.3): buckling class now depends on fy (<= 420 MPa or > 420 MPa).
* cl. 14.4.1: concrete bearing strength = min(0.45 fck sqrt(A1/A2), 0.9 fck).
* cl. 15.2.2: lateral torsional buckling rewritten (alpha_LT in Table 13, moment gradient factor f_M in Table 14,
  new chi_LT / phi_LT equations).
* Tension, bolt, weld provisions (Sec. 13 and Sec. 17): same formulas, only renumbered.

Assumptions and draft typos are listed in the docstring of the function they affect
(search for "Assumption" in this file).

@author: <Arriswin.S>
"""
import math

try:  # inside the Osdag package
    from ...Common import *
except ImportError:
    try:  # stand-alone use, with Common.py next to this file
        from Common import *
    except ImportError:  # minimal fall-back so that this module can be imported and tested on its own
        KEY_DP_FAB_SHOP = 'Shop Weld'
        KEY_DP_FAB_FIELD = 'Field Weld'


class IS800_2025(object):
    """Perform calculations on steel design as per IS 800:2025 (Draft)

    """

    # ==========================================================================
    """    SECTION  1 - 8   GENERAL (promoted from the sub-clauses of Section 1 in IS 800:2007)   """
    # ==========================================================================
    """    SECTION  9     MATERIALS   """
    # ==========================================================================
    """    SECTION  10    GENERAL DESIGN REQUIREMENTS   """
    # -------------------------------------------------------------
    #   10.8 Classification of Cross-Sections
    # -------------------------------------------------------------

    @staticmethod
    def _section_class_number(section_class):
        """Convert the name of a section class into its number (1 - 4)

        Args:
            section_class: 'Plastic' / 'Compact' / 'Semi-compact' / 'Slender' or 1 / 2 / 3 / 4 (str or int)

        Returns:
            Class number (int)
        """
        names = {'plastic': 1, 'class1': 1, 'class 1': 1, '1': 1,
                 'compact': 2, 'class2': 2, 'class 2': 2, '2': 2,
                 'semi-compact': 3, 'semi_compact': 3, 'semicompact': 3, 'class3': 3, 'class 3': 3, '3': 3,
                 'slender': 4, 'class4': 4, 'class 4': 4, '4': 4}
        key = str(section_class).strip().lower()
        if key not in names:
            raise ValueError("Unknown section class: {}".format(section_class))
        return names[key]

    @staticmethod
    def Table2_stress_ratios(depth_under_compression, overall_depth, sigma_min, sigma_max):
        """Calculate the stress ratios r_1 and r_2 as defined in Note 5 of Table 2

        Args:
            depth_under_compression: depth of the web that is under compression in mm (float)
            overall_depth: overall depth of the web in mm (float)
            sigma_min: minimum compressive stress in MPa, negative if it is tensile (float)
            sigma_max: maximum compressive stress in MPa (float)

        Returns:
            [r_1, r_2] (list of float)

        Note:
            Reference:
            IS 800:2025, Table 2, Note 5 (cl. 10.8)
            r_1 = depth under compression / overall depth
            r_2 = minimum compressive stress (tensile if negative) / maximum compressive stress
            (In IS 800:2007 r_1 was the ratio of the actual average axial stress to the design compressive stress.)
        """
        r_1 = depth_under_compression / overall_depth
        r_2 = sigma_min / sigma_max
        return [r_1, r_2]

    @staticmethod
    def Table2_i_outstand(width, thickness, f_y, section_class='Plastic', stress_type='Uniform compression',
                          r_1=None, tip='compression'):
        """Check the limiting width to thickness ratio of an outstanding element (e.g. flange of an I section)

        Args:
            width: outstand width b of the element in mm (float)
            thickness: thickness t_f of the element in mm (float)
            f_y: yield stress of the material in MPa (float)
            section_class: 'Plastic', 'Compact' or 'Semi-compact' (str)
            stress_type: 'Uniform compression' or 'Non uniform' (str)
            r_1: stress ratio r_1 of Note 5, needed for 'Non uniform' (float)
            tip: 'compression' or 'tension', position of the free tip when stress is non uniform (str)

        Returns:
            'Pass' if the element satisfies the limit of the given class, 'Fail' if it does not,
            'Not applicable' where the draft gives no limit (non uniform stress, Semi-compact) (str)

        Note:
            Reference:
            IS 800:2025, Table 2, row (i) (cl. 10.8)
            Limits for uniform compression : 8.7e / 9.7e / 13.6e (2007 : rolled 9.4e / 10.5e / 15.7e, welded 8.4e / 9.4e / 13.6e)
            Assumption: in 2025 rolled and welded outstands are merged into a single row.
        """
        epsilon = math.sqrt(250 / f_y)
        ratio = width / thickness
        cls = IS800_2025._section_class_number(section_class)
        if cls > 3:
            raise ValueError("Table 2 gives limits only for Class 1 to Class 3")

        if stress_type == 'Uniform compression':
            limit = {1: 8.7 * epsilon, 2: 9.7 * epsilon, 3: 13.6 * epsilon}[cls]
        else:
            if cls == 3:
                return 'Not applicable'
            if r_1 is None or r_1 <= 0:
                raise ValueError("r_1 (> 0) is required for non uniform stress")
            coefficient = {1: 8.7, 2: 9.7}[cls]
            if tip == 'compression':
                limit = coefficient * epsilon / r_1
            else:
                limit = coefficient * epsilon / (r_1 * math.sqrt(r_1))
        return 'Pass' if ratio <= limit else 'Fail'

    @staticmethod
    def Table2_ii_web(depth, thickness, f_y, section_class='Plastic', stress_type='Neutral axis at mid-depth',
                      r_1=None, r_2=None):
        """Check the limiting width to thickness ratio of the web of an I, Channel, H or box section

        Args:
            depth: clear depth d of the web in mm (float)
            thickness: thickness t_w of the web in mm (float)
            f_y: yield stress of the material in MPa (float)
            section_class: 'Plastic', 'Compact' or 'Semi-compact' (str)
            stress_type: 'Axial compression', 'Neutral axis at mid-depth' or 'Non uniform' (str)
            r_1: stress ratio r_1 of Note 5, needed for Class 1 and 2 when stress is 'Non uniform' (float)
            r_2: stress ratio r_2 of Note 5, needed for Class 3 when stress is 'Non uniform' (float)

        Returns:
            'Pass' if the web satisfies the limit of the given class, 'Fail' if it does not (str)

        Note:
            Reference:
            IS 800:2025, Table 2, row (ii) (cl. 10.8)
            Axial compression       : 32e / 36.8e / 40.7e
            Neutral axis at mid     : 70e / 80e / 120e
            Non uniform, Class 1    : 384e / (13 r_1 - 1) if r_1 > 0.5, else 35e / r_1
            Non uniform, Class 2    : 442e / (13 r_1 - 1) if r_1 > 0.5, else 40.2e / r_1
            Non uniform, Class 3    : 40.7e / (0.67 + 0.33 r_2) if r_2 > -1, else 60e (1 - r_2) sqrt(-r_2)

            Assumptions (draft typos / ambiguities):
            1. The 'Axial compression' limits are printed against the ratio "b/t_f" in the draft; they are applied here to d/t_w
               of the web (they are the internal-element limits of Eurocode 3 scaled by sqrt(235/250)).
            2. The last sub-row of the draft prints "r_2 > -1" twice and omits the minus sign inside the root;
               it is read as r_2 <= -1 and sqrt(-r_2), which makes the limit continuous at r_2 = -1 (about 120e).
        """
        epsilon = math.sqrt(250 / f_y)
        ratio = depth / thickness
        cls = IS800_2025._section_class_number(section_class)
        if cls > 3:
            raise ValueError("Table 2 gives limits only for Class 1 to Class 3")

        if stress_type == 'Axial compression':
            limit = {1: 32 * epsilon, 2: 36.8 * epsilon, 3: 40.7 * epsilon}[cls]
        elif stress_type == 'Neutral axis at mid-depth':
            limit = {1: 70 * epsilon, 2: 80 * epsilon, 3: 120 * epsilon}[cls]
        else:  # non uniform stress
            if cls in (1, 2):
                if r_1 is None or r_1 <= 0:
                    raise ValueError("r_1 (> 0) is required for Class 1 and Class 2 webs under non uniform stress")
                if r_1 > 0.5:
                    limit = {1: 384, 2: 442}[cls] * epsilon / (13 * r_1 - 1)
                else:
                    limit = {1: 35, 2: 40.2}[cls] * epsilon / r_1
            else:
                if r_2 is None:
                    raise ValueError("r_2 is required for Class 3 webs under non uniform stress")
                if r_2 > -1:
                    limit = 40.7 * epsilon / (0.67 + 0.33 * r_2)
                else:
                    limit = 60 * epsilon * (1 - r_2) * math.sqrt(-r_2)
        return 'Pass' if ratio <= limit else 'Fail'

    @staticmethod
    def Table2_iii_angle_bending(b, d, t, f_y, section_class='Plastic'):
        """Check an angle section in which the compression is due to bending (both b/t and d/t must be satisfied)

        Args:
            b: width of the leg in mm (float)
            d: depth of the leg in mm (float)
            t: thickness of the leg in mm (float)
            f_y: yield stress of the material in MPa (float)
            section_class: 'Plastic', 'Compact' or 'Semi-compact' (str)

        Returns:
            'Pass' if both the criteria are satisfied, 'Fail' if not (str)

        Note:
            Reference:
            IS 800:2025, Table 2, row (iii) (cl. 10.8)
            Limits : 8.7e / 9.7e / 14.5e (2007 : 9.4e / 10.5e / 15.7e)
        """
        epsilon = math.sqrt(250 / f_y)
        cls = IS800_2025._section_class_number(section_class)
        if cls > 3:
            raise ValueError("Table 2 gives limits only for Class 1 to Class 3")
        limit = {1: 8.7 * epsilon, 2: 9.7 * epsilon, 3: 14.5 * epsilon}[cls]
        return 'Pass' if (b / t <= limit and d / t <= limit) else 'Fail'

    @staticmethod
    def Table2_iv_angle_axial(b, d, t, f_y, section_class='Semi-compact'):
        """Check a single angle, or double angles with the components separated, under axial compression
        (all three criteria b/t, d/t and (b+d)/t must be satisfied)

        Args:
            b: width of the leg in mm (float)
            d: depth of the leg in mm (float)
            t: thickness of the leg in mm (float)
            f_y: yield stress of the material in MPa (float)
            section_class: only 'Semi-compact' has limits (str)

        Returns:
            'Pass' if all three criteria are satisfied, 'Fail' if not,
            'Not applicable' for Class 1 and Class 2 (str)

        Note:
            Reference:
            IS 800:2025, Table 2, row (iv) (cl. 10.8)
            Limits (Class 3) : b/t <= 14.5e, d/t <= 14.5e, (b+d)/t <= 22.3e (2007 : 15.7e, 15.7e, 25e)
        """
        epsilon = math.sqrt(250 / f_y)
        cls = IS800_2025._section_class_number(section_class)
        if cls != 3:
            return 'Not applicable'
        ok = (b / t <= 14.5 * epsilon) and (d / t <= 14.5 * epsilon) and ((b + d) / t <= 22.3 * epsilon)
        return 'Pass' if ok else 'Fail'

    @staticmethod
    def Table2_v_angle_leg_in_contact(d, t, f_y, section_class='Plastic'):
        """Check the outstanding leg of an angle in contact back-to-back in a double angle member or with another component

        Args:
            d: depth of the leg in mm (float)
            t: thickness of the leg in mm (float)
            f_y: yield stress of the material in MPa (float)
            section_class: 'Plastic', 'Compact' or 'Semi-compact' (str)

        Returns:
            'Pass' if the limit is satisfied, 'Fail' if not (str)

        Note:
            Reference:
            IS 800:2025, Table 2, row (v) (cl. 10.8)
            Limits : 8.7e / 9.7e / 14.5e
        """
        epsilon = math.sqrt(250 / f_y)
        cls = IS800_2025._section_class_number(section_class)
        if cls > 3:
            raise ValueError("Table 2 gives limits only for Class 1 to Class 3")
        limit = {1: 8.7 * epsilon, 2: 9.7 * epsilon, 3: 14.5 * epsilon}[cls]
        return 'Pass' if d / t <= limit else 'Fail'

    @staticmethod
    def Table2_vi_circular_hollow_tube(outer_diameter, tube_thickness, f_y, load_type='Moment', section_class='Plastic'):
        """Check a circular hollow tube (including welded tube)

        Args:
            outer_diameter: outer diameter D in mm (float)
            tube_thickness: thickness t in mm (float)
            f_y: yield stress of the material in MPa (float)
            load_type: 'Moment' or 'Axial compression' (str)
            section_class: 'Plastic', 'Compact' or 'Semi-compact' (str)

        Returns:
            'Pass' if the limit is satisfied, 'Fail' if not,
            'Not applicable' for Class 1 and Class 2 under axial compression (str)

        Note:
            Reference:
            IS 800:2025, Table 2, row (vi) (cl. 10.8)
            Moment            : 47e^2 / 66e^2 / 85e^2 (2007 : 42e^2 / 52e^2 / 146e^2)
            Axial compression : 86e^2 for Class 3 only (2007 : 88e^2)
        """
        epsilon_sq = 250 / f_y
        cls = IS800_2025._section_class_number(section_class)
        if cls > 3:
            raise ValueError("Table 2 gives limits only for Class 1 to Class 3")
        ratio = outer_diameter / tube_thickness
        if load_type == 'Moment':
            limit = {1: 47 * epsilon_sq, 2: 66 * epsilon_sq, 3: 85 * epsilon_sq}[cls]
        else:
            if cls != 3:
                return 'Not applicable'
            limit = 86 * epsilon_sq
        return 'Pass' if ratio <= limit else 'Fail'

    # -------------------------------------------------------------
    #   10.9 Maximum Effective Slenderness Ratio
    # -------------------------------------------------------------

    @staticmethod
    def cl_10_9_max_slenderness_ratio(Type=1):
        """Maximum values of effective slenderness ratio KL/r as per Table 3

        Args:
            Type: number of the row of Table 3 (int)
                1) A member carrying compressive loads resulting from dead loads and imposed loads
                2) A tension member in which a reversal of direct stress occurs due to loads other than wind or seismic forces
                3) A member subjected to compression forces resulting only from combination with wind/earthquake effects,
                   provided the deformation of such member does not adversely affect the stress in any part of the structure
                4) Compression flange of a beam against lateral torsional buckling
                5) A member normally acting as a tie in a roof truss or a bracing system not considered effective when
                   subject to possible reversal of stress into compression resulting from the action of wind or earthquake
                6) Members always under tension (other than pre-tensioned members)

        Returns:
            Maximum effective slenderness ratio KL/r (int)

        Note:
            Reference:
            IS 800:2025, Table 3 (cl. 10.9.1)
            The limits (180, 180, 250, 300, 350, 400) are the same as in IS 800:2007 Table 3 (cl. 3.8).
            The 2007 Osdag function returned 180 for every Type; here every Type returns its own limit.
            Tension members such as bracings, where sag is avoided, need not satisfy these limits (Table 3, footnote 1).
        """
        table_3 = {1: 180, 2: 180, 3: 250, 4: 300, 5: 350, 6: 400}
        if Type not in table_3:
            raise ValueError("Type must be 1 to 6")
        return table_3[Type]

    # ==========================================================================
    """    SECTION  11    METHODS OF STRUCTURAL ANALYSIS   """
    # ==========================================================================
    """    SECTION  12    LIMIT STATE DESIGN   """
    # -------------------------------------------------------------
    #   12.4 Strength
    # -------------------------------------------------------------
    # Table 5 Partial Safety Factors for Materials, gamma_m (dict) (cl. 12.4.1)
    # Values are the same as Table 5 of IS 800:2007
    cl_12_4_1_Table_5 = {"gamma_m0": {'yielding': 1.10, 'buckling': 1.10},
                         "gamma_m1": {'ultimate_stress': 1.25},
                         "gamma_mf": {KEY_DP_FAB_SHOP: 1.25, KEY_DP_FAB_FIELD: 1.25},
                         "gamma_mb": {KEY_DP_FAB_SHOP: 1.25, KEY_DP_FAB_FIELD: 1.25},
                         "gamma_mr": {KEY_DP_FAB_SHOP: 1.25, KEY_DP_FAB_FIELD: 1.25},
                         "gamma_mw": {KEY_DP_FAB_SHOP: 1.25, KEY_DP_FAB_FIELD: 1.50}
                         }

    # ==========================================================================
    """    SECTION  13    DESIGN OF TENSION MEMBERS   """
    # -------------------------------------------------------------
    #   13.2 Design Strength Due to Yielding of Gross Section
    # -------------------------------------------------------------

    @staticmethod
    def cl_13_2_tension_yielding_strength(A_g, f_y):
        """Calculate the design strength of a member in tension as governed by yielding of gross section

        Args:
            A_g: gross area of cross section in sq. mm (float)
            f_y: yield stress of the material in MPa (float)

        Returns:
            T_dg - design strength in tension yielding in N (float)

        Note:
            Reference:
            IS 800:2025, cl. 13.2 (IS 800:2007, cl. 6.2) - formula unchanged
        """
        gamma_m0 = IS800_2025.cl_12_4_1_Table_5["gamma_m0"]['yielding']
        T_dg = A_g * f_y / gamma_m0
        return T_dg

    # -------------------------------------------------------------
    #   13.3 Design Strength Due to Rupture of Critical Section
    # -------------------------------------------------------------

    @staticmethod
    def cl_13_3_1_net_effective_area_plate(b, t, n, d_h, staggers=None, punched=False):
        """Calculate the net effective area of a plate with bolt holes

        Args:
            b: width of the plate in mm (float)
            t: thickness of the plate in mm (float)
            n: number of bolt holes in the critical section (int)
            d_h: diameter of the bolt hole in mm (float)
            staggers: list of (p_s, g) pairs, one for every inclined leg - staggered pitch and gauge in mm (list of tuples)
            punched: True for directly punched holes, 2 mm is added to the hole diameter (bool)

        Returns:
            A_n - net effective area in sq. mm (float)

        Note:
            Reference:
            IS 800:2025, cl. 13.3.1, Fig. 5
            A_n = [ b - n d_h + sum( p_s^2 / (4 g) ) ] t
        """
        if punched:
            d_h = d_h + 2.0
        stagger_term = 0.0
        if staggers:
            for p_s, g in staggers:
                stagger_term += p_s ** 2 / (4.0 * g)
        return (b - n * d_h + stagger_term) * t

    @staticmethod
    def cl_13_3_1_tension_rupture_strength(A_n, f_u):
        """Calculate the design strength in tension of a plate as governed by rupture of net cross section

        Args:
            A_n: net effective area of member in sq. mm (float)
            f_u: ultimate stress of the material in MPa (float)

        Returns:
            T_dn - design strength in tension rupture in N (float)

        Note:
            Reference:
            IS 800:2025, cl. 13.3.1 (IS 800:2007, cl. 6.3.1) - formula unchanged
        """
        gamma_m1 = IS800_2025.cl_12_4_1_Table_5["gamma_m1"]['ultimate_stress']
        T_dn = 0.9 * A_n * f_u / gamma_m1
        return T_dn

    @staticmethod
    def cl_13_3_2_threaded_rod_rupture_strength(A_n, f_u):
        """Calculate the design strength in tension of a threaded rod as governed by rupture

        Args:
            A_n: net root area at the threaded section in sq. mm (float)
            f_u: ultimate stress of the material in MPa (float)

        Returns:
            T_dn - design strength in N (float)

        Note:
            Reference:
            IS 800:2025, cl. 13.3.2
        """
        gamma_m1 = IS800_2025.cl_12_4_1_Table_5["gamma_m1"]['ultimate_stress']
        return 0.9 * A_n * f_u / gamma_m1

    @staticmethod
    def cl_13_3_3_shear_lag_factor_beta(w, t, b_s, L_c, f_y, f_u):
        """Calculate the shear lag factor beta of an angle connected through one leg

        Args:
            w: width of the outstand leg in mm (float)
            t: thickness of the leg in mm (float)
            b_s: shear lag width as shown in Fig. 6 in mm (float)
            L_c: length of the end connection in mm - distance between the outermost bolts in the end joint
                 measured along the load direction, or the length of the weld along the load direction (float)
            f_y: yield stress of the material in MPa (float)
            f_u: ultimate stress of the material in MPa (float)

        Returns:
            beta - shear lag factor (float)

        Note:
            Reference:
            IS 800:2025, cl. 13.3.3
            beta = 1.4 - 0.076 (w/t) (f_y/f_u) (b_s/L_c), with 0.7 <= beta <= 0.9 f_u gamma_m0 / (f_y gamma_m1)
            The upper bound includes the factor 0.9 that was added to IS 800:2007 by Amendment No. 1 (2012).
        """
        gamma_m0 = IS800_2025.cl_12_4_1_Table_5["gamma_m0"]['yielding']
        gamma_m1 = IS800_2025.cl_12_4_1_Table_5["gamma_m1"]['ultimate_stress']
        beta = 1.4 - 0.076 * (w / t) * (f_y / f_u) * (b_s / L_c)
        beta = min(beta, 0.9 * f_u * gamma_m0 / (f_y * gamma_m1))
        beta = max(beta, 0.7)
        return beta

    @staticmethod
    def cl_13_3_3_single_angle_rupture_strength(A_nc, A_go, w, t, b_s, L_c, f_y, f_u):
        """Calculate the design strength of an angle connected through one leg as governed by rupture at the net section

        Args:
            A_nc: net area of the connected leg in sq. mm (float)
            A_go: gross area of the outstanding leg in sq. mm (float)
            w: width of the outstand leg in mm (float)
            t: thickness of the leg in mm (float)
            b_s: shear lag width in mm (float)
            L_c: length of the end connection in mm (float)
            f_y: yield stress of the material in MPa (float)
            f_u: ultimate stress of the material in MPa (float)

        Returns:
            T_dn - design strength in N (float)

        Note:
            Reference:
            IS 800:2025, cl. 13.3.3 (also used for other sections by cl. 13.3.4, where b_s is measured from
            the farthest edge of the outstanding leg to the nearest bolt/weld line in the connected leg)
            T_dn = 0.9 A_nc f_u / gamma_m1 + beta A_go f_y / gamma_m0
        """
        gamma_m0 = IS800_2025.cl_12_4_1_Table_5["gamma_m0"]['yielding']
        gamma_m1 = IS800_2025.cl_12_4_1_Table_5["gamma_m1"]['ultimate_stress']
        beta = IS800_2025.cl_13_3_3_shear_lag_factor_beta(w, t, b_s, L_c, f_y, f_u)
        return 0.9 * A_nc * f_u / gamma_m1 + beta * A_go * f_y / gamma_m0

    # -------------------------------------------------------------
    #   13.4 Design Strength Due to Block Shear
    # -------------------------------------------------------------

    @staticmethod
    def cl_13_4_1_block_shear_strength(A_vg, A_vn, A_tg, A_tn, f_u, f_y):
        """Calculate the block shear strength of bolted connections as per cl. 13.4.1

        Args:
            A_vg: Minimum gross area in shear along bolt line parallel to external force [in sq. mm] (float)
            A_vn: Minimum net area in shear along bolt line parallel to external force [in sq. mm] (float)
            A_tg: Minimum gross area in tension from the bolt hole to the toe of the angle,
                  end bolt line, perpendicular to the line of force, respectively [in sq. mm] (float)
            A_tn: Minimum net area in tension from the bolt hole to the toe of the angle,
                  end bolt line, perpendicular to the line of force, respectively [in sq. mm] (float)
            f_u: Ultimate stress of the plate material in MPa (float)
            f_y: Yield stress of the plate material in MPa (float)

        Returns:
            block shear strength of bolted connection in N (float)

        Note:
            Reference:
            IS 800:2025, cl. 13.4.1 (IS 800:2007, cl. 6.4.1) - formula unchanged
        """
        gamma_m0 = IS800_2025.cl_12_4_1_Table_5["gamma_m0"]['yielding']
        gamma_m1 = IS800_2025.cl_12_4_1_Table_5["gamma_m1"]['ultimate_stress']
        T_db1 = A_vg * f_y / (math.sqrt(3) * gamma_m0) + 0.9 * A_tn * f_u / gamma_m1
        T_db2 = 0.9 * A_vn * f_u / (math.sqrt(3) * gamma_m1) + A_tg * f_y / gamma_m0
        return min(T_db1, T_db2)

    # ==========================================================================
    """    SECTION  14    DESIGN OF COMPRESSION MEMBERS   """
    # -------------------------------------------------------------
    #   14.1 Design Strength
    # -------------------------------------------------------------

    @staticmethod
    def cl_14_1_2_design_compressive_strength_member(effective_area, design_compressive_stress, axial_load):
        """Check the factored design compression P against the design compressive strength P_d = A_e f_cd

        Args:
            effective_area: effective sectional area as defined in cl. 14.3.2 in sq. mm (float)
            design_compressive_stress: design compressive stress f_cd as per cl. 14.1.2 in MPa (float)
            axial_load: factored axial compression acting on the member in N (float)

        Returns:
            'pass' if P < P_d, 'fail' otherwise (str)

        Note:
            Reference:
            IS 800:2025, cl. 14.1.2 (IS 800:2007, cl. 7.1.2)
        """
        design_compressive_strength = effective_area * design_compressive_stress  # N
        if axial_load < design_compressive_strength:
            check = 'pass'
        else:
            check = 'fail'
        return check

    @staticmethod
    def cl_14_1_2_1_design_compressive_stress(f_y, gamma_mo, effective_slenderness_ratio, imperfection_factor,
                                              modulus_of_elasticity, check_type):
        """Calculate the design compressive stress f_cd for flexural buckling

        Args:
            f_y: Yield stress in MPa (float)
            gamma_mo: Partial safety factor against yield stress and buckling (float)
            effective_slenderness_ratio: effective slenderness ratio KL/r (float)
            imperfection_factor: alpha, from Table 7 (float)
            modulus_of_elasticity: E in MPa (float)
            check_type: contains 'Concentric' for a concentrically loaded member; for an angle loaded through one leg a
                        sequence ('Leg', lambda_e) is given where lambda_e is the equivalent slenderness ratio (str or tuple)

        Returns:
            [euler_buckling_stress, nondimensional_effective_slenderness_ratio, phi, stress_reduction_factor,
             design_compressive_stress_fr, design_compressive_stress, design_compressive_stress_max]

        Note:
            Reference:
            IS 800:2025, cl. 14.1.2.1 (IS 800:2007, cl. 7.1.2.1)
            chi = 1 / ( phi + sqrt(phi^2 - lambda^2) ),  phi = 0.5 [ 1 + alpha (lambda - 0.2) + lambda^2 ]
            Assumption: the extracted text of the draft prints "phi^2 + lambda^2" under the root; Tables 8 and 9 of the same
            draft (and IS 800:2007) are consistent with "phi^2 - lambda^2", so the minus sign is used.
        """
        # Euler buckling stress
        euler_buckling_stress = (math.pi ** 2 * modulus_of_elasticity) / effective_slenderness_ratio ** 2
        if 'Concentric' in check_type:
            # Non-dimensional effective slenderness ratio
            nondimensional_effective_slenderness_ratio = math.sqrt(f_y / euler_buckling_stress)
        elif 'Leg' in check_type:
            nondimensional_effective_slenderness_ratio = check_type[1]
        else:
            raise ValueError("check_type must contain 'Concentric' or be ('Leg', lambda_e)")
        phi = 0.5 * (1 + imperfection_factor * (nondimensional_effective_slenderness_ratio - 0.2)
                     + nondimensional_effective_slenderness_ratio ** 2)
        # Design compressive stress
        stress_reduction_factor = 1 / (phi + math.sqrt(phi ** 2 - nondimensional_effective_slenderness_ratio ** 2))
        design_compressive_stress_fr = f_y * stress_reduction_factor / gamma_mo
        design_compressive_stress_max = f_y / gamma_mo
        design_compressive_stress = min(design_compressive_stress_fr, design_compressive_stress_max)
        return [euler_buckling_stress, nondimensional_effective_slenderness_ratio, phi, stress_reduction_factor,
                design_compressive_stress_fr, design_compressive_stress, design_compressive_stress_max]

    @staticmethod
    def cl_14_1_2_3_imperfection_factor(buckling_class=''):
        """Determine the imperfection factor of the cross-section as per Table 7 of IS 800:2025

        Args:
            buckling_class: 'a0', 'a', 'b', 'c' or 'd' (str)

        Returns:
            Imperfection factor value (float)

        Note:
            Reference:
            IS 800:2025, cl. 14.1.1, cl. 14.1.2, Table 7
            New in 2025: buckling class a0 with alpha = 0.13. Other values are unchanged (0.21, 0.34, 0.49, 0.76).
        """
        imperfection_factor = {
            'a0': 0.13,
            'a': 0.21,
            'b': 0.34,
            'c': 0.49,
            'd': 0.76
        }[buckling_class]
        return imperfection_factor

    @staticmethod
    def cl_14_1_2_3_buckling_class_of_crosssections(b, h, t_f, f_y, cross_section='Rolled I-sections',
                                                    section_type='Hot rolled', thick_welds=False,
                                                    b_by_t_f=None, h_by_t_w=None):
        """Determine the buckling class of the cross-section as per Table 10 of IS 800:2025

        Args:
            b: width of the flange b_f in mm (float)
            h: depth of the section in mm (float)
            t_f: thickness of the flange in mm (float)
            f_y: yield stress of the material in MPa (float) - NEW in 2025, the class depends on f_y <= 420 or > 420
            cross_section: 'Rolled I-sections', 'Welded I-section', 'Hollow Section', 'Welded Box Section, Cruciform',
                           'Channel, Angle, T and Solid Sections', 'Built-up Member (Rolled Sections)'
                           or 'Built-up Member (Welded Sections)' (str)
            section_type: 'Hot rolled' or 'Cold formed' - only for 'Hollow Section' (str)
            thick_welds: True for a welded box section with thick welds (bool)
            b_by_t_f: b/t_f of a welded box section, used with thick_welds (float)
            h_by_t_w: h/t_w of a welded box section, used with thick_welds (float)

        Returns:
            Buckling class values about z-z and y-y axis (dictionary)

        Note:
            Reference:
            IS 800:2025, cl. 14.1.2.3, Table 10 (IS 800:2007, cl. 7.1.2.2, Table 10)
            Assumptions:
            1. The draft has no row for a rolled I section with h/b_f > 1.2 and t_f > 100 mm. The class of the h/b_f <= 1.2,
               t_f > 100 mm row (d, d for f_y <= 420 MPa; c, c for f_y > 420 MPa) is used, as the 2007 Osdag code did.
            2. The printed boundary h/b_f = 1.2 is assigned to the second (h/b_f <= 1.2) group.
            3. For a welded box section the thick-weld rule is applied about z-z when b/t_f < 30 and about y-y when h/t_w < 30.
        """
        high_strength = f_y > 420  # column (5) of Table 10

        def pick(normal, high):
            return high if high_strength else normal

        if cross_section == 'Rolled I-sections':
            if h / b > 1.2:
                if t_f <= 40:
                    buckling_class = {'z-z': pick('a', 'a0'), 'y-y': pick('b', 'a')}
                elif t_f <= 100:
                    buckling_class = {'z-z': pick('b', 'a'), 'y-y': pick('c', 'b')}
                else:  # not given in the draft (assumption 1)
                    buckling_class = {'z-z': pick('d', 'c'), 'y-y': pick('d', 'c')}
            else:
                if t_f <= 100:
                    buckling_class = {'z-z': pick('b', 'a'), 'y-y': pick('c', 'b')}
                else:
                    buckling_class = {'z-z': pick('d', 'c'), 'y-y': pick('d', 'c')}

        elif cross_section == 'Welded I-section':
            if t_f <= 40:
                buckling_class = {'z-z': pick('b', 'b'), 'y-y': pick('c', 'c')}
            else:
                buckling_class = {'z-z': pick('c', 'c'), 'y-y': pick('d', 'd')}

        elif cross_section == 'Hollow Section':
            if section_type == 'Hot rolled':
                buckling_class = {'z-z': pick('a', 'a0'), 'y-y': pick('a', 'a0')}
            else:  # Cold formed
                buckling_class = {'z-z': pick('b', 'c'), 'y-y': pick('b', 'c')}

        elif cross_section == 'Welded Box Section, Cruciform':
            buckling_class = {'z-z': 'b', 'y-y': 'b'}
            if thick_welds:
                if b_by_t_f is not None and b_by_t_f < 30:
                    buckling_class['z-z'] = 'c'
                if h_by_t_w is not None and h_by_t_w < 30:
                    buckling_class['y-y'] = 'c'

        elif cross_section == 'Channel, Angle, T and Solid Sections':
            buckling_class = {'z-z': 'c', 'y-y': 'c'}

        elif cross_section == 'Built-up Member (Rolled Sections)':
            buckling_class = {'z-z': pick('b', 'a'), 'y-y': pick('b', 'a')}

        elif cross_section == 'Built-up Member (Welded Sections)':  # t <= 40 mm
            buckling_class = {'z-z': 'c', 'y-y': 'c'}

        else:
            raise ValueError("Unknown cross_section: {}".format(cross_section))

        return buckling_class

    # -------------------------------------------------------------
    #   14.4 Column Bases
    # -------------------------------------------------------------

    @staticmethod
    def cl_14_4_1_bearing_strength_concrete(concrete_grade, A_1=None, A_2=None):
        """Calculate the bearing strength of the concrete pedestal/footing below a base plate

        Args:
            concrete_grade: grade of concrete used for pedestal/footing, e.g. 'M25' (str)
            A_1: area of the concrete pedestal on which the base plate is sitting in sq. mm (float)
            A_2: surface area of the steel base plate transferring the load to the pedestal in sq. mm (float)
                 If A_1 or A_2 is not given, sqrt(A_1/A_2) is taken as 1.0 (this is the 0.45 f_ck of the 2007 Osdag code).

        Returns:
            Maximum permissible bearing strength of the concrete in MPa (float)

        Note:
            Reference:
            IS 800:2025, cl. 14.4.1 (IS 800:2007, cl. 7.4.1 gave 0.60 f_ck, amended to 0.45 f_ck in the Osdag code)
            bearing strength = smaller of 0.45 f_ck sqrt(A_1/A_2) and 0.9 f_ck
            f_ck is the smaller of the characteristic cube strength of concrete or of the bedding material.
        """
        f_ck = {
            'M10': 10,
            'M15': 15,
            'M20': 20,
            'M25': 25,
            'M30': 30,
            'M35': 35,
            'M40': 40,
            'M45': 45,
            'M50': 50,
            'M55': 55,
        }[str(concrete_grade)]

        if A_1 is None or A_2 is None:
            area_ratio = 1.0
        else:
            if A_2 <= 0:
                raise ValueError("A_2 must be positive")
            area_ratio = A_1 / A_2

        bearing_strength = min(0.45 * f_ck * math.sqrt(area_ratio), 0.9 * f_ck)  # MPa (N/mm^2)
        return bearing_strength

    # ==========================================================================
    """    SECTION  15    DESIGN OF BENDING MEMBERS   """
    # -------------------------------------------------------------
    #   15.2 Design Strength Governed by Flexure
    # -------------------------------------------------------------

    @staticmethod
    def cl_15_2_2_imperfection_parameter_alpha_LT(section_type, h=None, b=None, t_f=None, Z_ez=None, Z_ey=None):
        """Determine the imperfection parameter alpha_LT for lateral torsional buckling as per Table 13

        Args:
            section_type: 'Rolled I or H', 'Welded I', 'Rolled unequal I or H', 'Welded unequal I' or 'Other rolled' (str)
            h: overall depth of the section in mm (float)
            b: flange width in mm. For unequal sections the smaller flange width b_min is used (float)
            t_f: flange thickness in mm (float)
            Z_ez: elastic section modulus about the major (z-z) axis in cu. mm (float)
            Z_ey: elastic section modulus about the minor (y-y) axis in cu. mm (float)

        Returns:
            alpha_LT (float)

        Note:
            Reference:
            IS 800:2025, cl. 15.2.2, Table 13 (2007 : 0.21 for rolled and 0.49 for welded sections, Table 14)
            Rolled I or H, h/b > 1.2, t_f <= 40 mm  : 0.12 sqrt(Z_ez/Z_ey) <= 0.34
            Rolled I or H, h/b > 1.2, t_f >  40 mm  : 0.16 sqrt(Z_ez/Z_ey) <= 0.49
            Rolled I or H, h/b <= 1.2               : 0.12 sqrt(Z_ez/Z_ey) <= 0.34
            Welded I, t_f <= 40 mm and t_f > 40 mm  : 0.12 sqrt(Z_ez/Z_ey) <= 0.34
            Rolled unequal I or H : 0.21 (h/b_min <= 2.0), 0.34 (h/b_min > 2.0)
            Welded unequal I      : 0.49 (h/b_min <= 2.0), 0.76 (h/b_min > 2.0)
            Other rolled sections : 0.76

            Assumptions (draft typos):
            1. The third row of the rolled I/H group is printed with "h/b > 1.2" a second time. It is read as h/b <= 1.2.
            2. Both welded I rows print the same expression (0.12 ... <= 0.34). They are used as printed; this should be
               confirmed with BIS because the t_f > 40 mm row of the rolled section uses 0.16 and 0.49.
            3. Z_ez / Z_ey are the elastic moduli about the z-z (major) and y-y (minor) axes.
        """
        if section_type in ('Rolled I or H', 'Welded I'):
            if Z_ez is None or Z_ey is None:
                raise ValueError("Z_ez and Z_ey are required")
            ratio = math.sqrt(Z_ez / Z_ey)
            if section_type == 'Rolled I or H' and h / b > 1.2 and t_f > 40:
                return min(0.16 * ratio, 0.49)
            return min(0.12 * ratio, 0.34)
        elif section_type == 'Rolled unequal I or H':
            return 0.21 if h / b <= 2.0 else 0.34
        elif section_type == 'Welded unequal I':
            return 0.49 if h / b <= 2.0 else 0.76
        elif section_type == 'Other rolled':
            return 0.76
        raise ValueError("Unknown section_type: {}".format(section_type))

    @staticmethod
    def cl_15_2_2_moment_gradient_factor_f_M(load_case, psi=None, M0_by_Mh=None):
        """Determine the moment gradient effect parameter f_M as per Table 14

        Args:
            load_case: one of the following strings (str)
                'uniform moment'                           - M = uniform
                'linear moment'                            - end moments M and psi*M, needs psi (-1 <= psi <= 1)
                'udl'                                      - uniformly distributed load, simply supported, no end moments
                'udl with equal end moments'               - UDL plus equal end moments M_h, needs M0_by_Mh
                'udl with one end moment'                  - UDL plus one end moment M_h, needs M0_by_Mh
                'central point load'                       - central point load, no end moments
                'point load with equal end moments'        - central point load plus equal end moments M_h, needs M0_by_Mh
                'point load with one end moment'           - central point load plus one end moment M_h, needs M0_by_Mh
            psi: ratio of the end moments (float)
            M0_by_Mh: ratio of the free (mid-span) bending moment M_0 to the end moment M_h (float)

        Returns:
            f_M (float)

        Note:
            Reference:
            IS 800:2025, cl. 15.2.2, Table 14 (new in 2025)
            Assumption: the load cases with end moments are identified from the figures of the table; the table
            has no separate heading for them.
        """
        x = M0_by_Mh
        if load_case == 'uniform moment':
            return 1.0
        elif load_case == 'linear moment':
            if psi is None or not -1 <= psi <= 1:
                raise ValueError("psi between -1 and +1 is required")
            return 1.25 - 0.1 * psi - 0.15 * psi ** 2
        elif load_case == 'udl':
            return 1.05
        elif load_case == 'central point load':
            return 1.10

        if x is None or x < 0:
            raise ValueError("M0_by_Mh >= 0 is required for this load case")
        if load_case == 'udl with equal end moments':
            return 1.0 + 1.35 * x - 0.33 * x ** 3 if x < 2.0 else 1.05
        elif load_case == 'udl with one end moment':
            return 1.25 + 0.5 * x ** 2 - 0.275 * x ** 4 if x < 1.47 else 1.05
        elif load_case == 'point load with equal end moments':
            return 1.0 + 1.25 * x - 0.30 * x ** 3 if x < 2.0 else 1.10
        elif load_case == 'point load with one end moment':
            return 1.25 + 0.325 * x ** 2 - 0.175 * x ** 4 if x < 1.5 else 1.10
        raise ValueError("Unknown load_case: {}".format(load_case))

    @staticmethod
    def cl_15_2_2_beta_b(section_class, Z_p, Z_e=None, Z_eff=None):
        """Calculate beta_b, the ratio used in the design bending strength of laterally unsupported beams

        Args:
            section_class: 'Plastic', 'Compact', 'Semi-compact' or 'Slender' (str)
            Z_p: plastic section modulus in cu. mm (float)
            Z_e: elastic section modulus with respect to the extreme compression fibre in cu. mm (float)
            Z_eff: effective section modulus of a Class 4 section in cu. mm (float)

        Returns:
            beta_b (float)

        Note:
            Reference:
            IS 800:2025, cl. 15.2.2
            beta_b = 1.0 (plastic, compact); Z_e / Z_p (semi-compact); Z_eff / Z_p (non-compact, Class 4 - new in 2025)
        """
        cls = IS800_2025._section_class_number(section_class)
        if cls <= 2:
            return 1.0
        elif cls == 3:
            return Z_e / Z_p
        return Z_eff / Z_p

    @staticmethod
    def cl_15_2_2_elastic_buckling_moment(E, mu, I_y, I_t, I_w, L_LT):
        """Calculate the elastic lateral torsional buckling moment of a simply supported prismatic symmetric member

        Args:
            E: modulus of elasticity in MPa (float)
            mu: Poisson's ratio (float)
            I_y: moment of inertia about the weaker axis in mm^4 (float)
            I_t: torsional constant in mm^4 (float)
            I_w: warping constant in mm^6 (float)
            L_LT: effective length for lateral torsional buckling in mm (float)

        Returns:
            M_cr in N-mm (float)

        Note:
            Reference:
            IS 800:2025, cl. 15.2.2.1
            M_cr = sqrt( (pi^2 E I_y / L_LT^2) (G I_t + pi^2 E I_w / L_LT^2) ),  G = E / (2 (1 + mu))
            The draft says that Annex E gives the more accurate method for other loading and support conditions.
        """
        G = E / (2 * (1 + mu))
        return math.sqrt((math.pi ** 2 * E * I_y / L_LT ** 2) * (G * I_t + math.pi ** 2 * E * I_w / L_LT ** 2))

    @staticmethod
    def cl_15_2_2_1_fcr_b_approx(E, L_LT_by_r_y, h_f_by_t_f):
        """Approximate extreme-fibre elastic lateral torsional buckling stress of non-slender rolled steel sections

        Args:
            E: modulus of elasticity in MPa (float)
            L_LT_by_r_y: ratio of the effective length for lateral torsional buckling to the radius of gyration
                         about the weaker axis (float)
            h_f_by_t_f: ratio of the centre to centre distance between flanges to the flange thickness (float)

        Returns:
            f_cr,b in MPa (float)

        Note:
            Reference:
            IS 800:2025, cl. 15.2.2.1
            f_cr,b = 1.1 pi^2 E / (L_LT/r_y)^2  *  sqrt( 1 + (1/20) ((L_LT/r_y) / (h_f/t_f))^2 )
            The 2007 Osdag function cl_8_2_2_Unsupported_beam_bending_fcrb divided by (L_LT/r_y) instead of (L_LT/r_y)^2.
        """
        return (1.1 * math.pi ** 2 * E / L_LT_by_r_y ** 2) * math.sqrt(1 + (L_LT_by_r_y / h_f_by_t_f) ** 2 / 20)

    @staticmethod
    def cl_15_2_2_non_dimensional_slenderness_lambda_LT(beta_b, Z_p, Z_e, f_y, M_cr):
        """Calculate the non-dimensional slenderness ratio lambda_LT for lateral torsional buckling

        Args:
            beta_b: ratio from cl. 15.2.2 (float)
            Z_p: plastic section modulus in cu. mm (float)
            Z_e: elastic section modulus in cu. mm (float)
            f_y: yield stress in MPa (float)
            M_cr: elastic lateral torsional buckling moment in N-mm (float)

        Returns:
            lambda_LT (float)

        Note:
            Reference:
            IS 800:2025, cl. 15.2.2
            lambda_LT = sqrt( beta_b Z_p f_y / M_cr ) <= sqrt( 1.2 Z_e f_y / M_cr )
        """
        return min(math.sqrt(beta_b * Z_p * f_y / M_cr), math.sqrt(1.2 * Z_e * f_y / M_cr))

    @staticmethod
    def cl_15_2_2_non_dimensional_slenderness_lambda_y(f_y, E, L, r_y):
        """Calculate the weak axis non-dimensional slenderness ratio lambda_y = sqrt(f_y / f_cry)

        Args:
            f_y: yield stress in MPa (float)
            E: modulus of elasticity in MPa (float)
            L: distance between the lateral supports to the compression flange in mm (float)
            r_y: radius of gyration about the weaker axis in mm (float)

        Returns:
            lambda_y (float)

        Note:
            Reference:
            IS 800:2025, cl. 15.2.2
            Assumption: f_cry is the Euler buckling stress pi^2 E / (L/r_y)^2 of the weaker axis for the length
            between the lateral supports of the compression flange.
        """
        f_cry = math.pi ** 2 * E / (L / r_y) ** 2
        return math.sqrt(f_y / f_cry)

    @staticmethod
    def cl_15_2_2_phi_LT(alpha_LT, lambda_LT, lambda_y, f_M):
        """Calculate phi_LT of the lateral torsional buckling curve

        Args:
            alpha_LT: imperfection parameter from Table 13 (float)
            lambda_LT: non-dimensional slenderness ratio for lateral torsional buckling (float)
            lambda_y: weak axis non-dimensional slenderness ratio (float)
            f_M: moment gradient effect parameter from Table 14 (float)

        Returns:
            phi_LT (float)

        Note:
            Reference:
            IS 800:2025, cl. 15.2.2 (IS 800:2007, cl. 8.2.2 : phi_LT = 0.5 [1 + alpha_LT (lambda_LT - 0.2) + lambda_LT^2])
            phi_LT = 0.5 [ 1 + f_M ( (lambda_LT / lambda_y)^2 alpha_LT (lambda_LT - 0.2) + lambda_LT^2 ) ]
        """
        return 0.5 * (1 + f_M * ((lambda_LT / lambda_y) ** 2 * alpha_LT * (lambda_LT - 0.2) + lambda_LT ** 2))

    @staticmethod
    def cl_15_2_2_chi_LT(phi_LT, lambda_LT, f_M):
        """Calculate the bending stress reduction factor chi_LT for lateral torsional buckling

        Args:
            phi_LT: value from cl_15_2_2_phi_LT (float)
            lambda_LT: non-dimensional slenderness ratio for lateral torsional buckling (float)
            f_M: moment gradient effect parameter from Table 14 (float)

        Returns:
            chi_LT, not more than 1.0 (float)

        Note:
            Reference:
            IS 800:2025, cl. 15.2.2 (IS 800:2007 : chi_LT = 1 / (phi_LT + sqrt(phi_LT^2 - lambda_LT^2)) <= 1.0)
            chi_LT = f_M / ( phi_LT + sqrt( phi_LT^2 - f_M lambda_LT^2 ) ) <= 1.0
        """
        chi_LT = f_M / (phi_LT + math.sqrt(phi_LT ** 2 - f_M * lambda_LT ** 2))
        return min(chi_LT, 1.0)

    @staticmethod
    def cl_15_2_2_lateral_torsional_buckling_check_not_needed(lambda_LT, bending_axis='major', hollow_or_solid=False):
        """Check whether the lateral torsional buckling check can be skipped

        Args:
            lambda_LT: non-dimensional slenderness ratio for lateral torsional buckling (float)
            bending_axis: 'major' or 'minor' (str)
            hollow_or_solid: True for hollow (rectangular/tubular) sections and solid bars (bool)

        Returns:
            True if the member may be treated as laterally supported (bool)

        Note:
            Reference:
            IS 800:2025, cl. 15.2.2 (a), (b), (c) - for major axis bending lambda_LT < 0.4 (2007 : 0.4 as well)
        """
        return bending_axis == 'minor' or hollow_or_solid or lambda_LT < 0.4

    @staticmethod
    def cl_15_2_2_design_bending_compressive_stress(chi_LT, f_y, gamma_mo=None):
        """Calculate the design bending compressive stress f_bd = chi_LT f_y / gamma_m0

        Args:
            chi_LT: bending stress reduction factor (float)
            f_y: yield stress in MPa (float)
            gamma_mo: partial safety factor, default from Table 5 (float)

        Returns:
            f_bd in MPa (float)

        Note:
            Reference:
            IS 800:2025, cl. 15.2.2
        """
        if gamma_mo is None:
            gamma_mo = IS800_2025.cl_12_4_1_Table_5["gamma_m0"]['yielding']
        return chi_LT * f_y / gamma_mo

    @staticmethod
    def cl_15_2_2_design_bending_strength(beta_b, Z_p, f_bd):
        """Calculate the design bending strength of a laterally unsupported beam, M_d = beta_b Z_p f_bd

        Args:
            beta_b: ratio from cl. 15.2.2 (float)
            Z_p: plastic section modulus in cu. mm (float)
            f_bd: design bending compressive stress in MPa (float)

        Returns:
            M_d in N-mm (float)

        Note:
            Reference:
            IS 800:2025, cl. 15.2.2
        """
        return beta_b * Z_p * f_bd

    # ==========================================================================
    """    SECTION  16    COMBINED FORCES   """
    # ==========================================================================
    """    SECTION  17    CONNECTIONS   """
    # -------------------------------------------------------------
    #   17.2 Spacing and Edge Distance
    # -------------------------------------------------------------

    @staticmethod
    def cl_17_2_1_bolt_hole_size(d, bolt_hole_type='Standard'):
        """Calculate bolt hole diameter as per Table 19 of IS 800:2025

        Args:
             d - Nominal diameter of fastener in mm (float)
             bolt_hole_type - Either 'Standard' or 'Over-sized' or 'short_slot' or 'long_slot' (str)

        Returns:
            bolt_hole_size -  Diameter of the bolt hole in mm (float)

        Note:
            Reference:
            IS 800:2025, Table 19 (Cl 17.2.1) - values unchanged from IS 800:2007 Table 19
        """
        table_19 = {
            "12-14": {'Standard': 1.0, 'Over-sized': 3.0, 'short_slot': 4.0, 'long_slot': 2.5},
            "16-22": {'Standard': 2.0, 'Over-sized': 4.0, 'short_slot': 6.0, 'long_slot': 2.5},
            "24": {'Standard': 2.0, 'Over-sized': 6.0, 'short_slot': 8.0, 'long_slot': 2.5},
            "24+": {'Standard': 3.0, 'Over-sized': 8.0, 'short_slot': 10.0, 'long_slot': 2.5}
        }
        d = int(d)

        if d < 12:
            clearance = 0
        elif d <= 14:
            clearance = table_19["12-14"][bolt_hole_type]
        elif d <= 22:
            clearance = table_19["16-22"][bolt_hole_type]
        elif d <= 24:
            clearance = table_19["24"][bolt_hole_type]
        else:
            clearance = table_19["24+"][bolt_hole_type]
        if bolt_hole_type == 'long_slot':
            bolt_hole_size = (clearance + 1) * d
        else:
            bolt_hole_size = clearance + d
        return bolt_hole_size

    @staticmethod
    def cl_17_2_2_min_spacing(d):
        """Calculate minimum distance between centre of fasteners

        Args:
             d - Nominal diameter of fastener in mm (float)

        Returns:
            Minimum distance between centre of fasteners in mm (float)

        Note:
            Reference:
            IS 800:2025, cl. 17.2.2
        """
        return 2.5 * d

    @staticmethod
    def cl_17_2_3_1_max_spacing(plate_thicknesses):
        """Calculate maximum distance between centre of fasteners

        Args:
             plate_thicknesses - List of thicknesses in mm of connected plates (list or tuple)

        Returns:
            Maximum distance between centres of adjacent fasteners in mm (float)

        Note:
            Reference:
            IS 800:2025, cl. 17.2.3.1
        """
        t = min(plate_thicknesses)
        return min(32 * t, 300.0)

    @staticmethod
    def cl_17_2_3_2_max_pitch_tension_compression(d, plate_thicknesses, member_type):
        """Calculate maximum pitch between centre of fasteners lying in the direction of stress

        Args:
             d - Nominal diameter of fastener in mm (float)
             plate_thicknesses - List of thicknesses in mm of connected plates (list or tuple)
             member_type - Either 'tension' or 'compression' or 'compression_butting' (str)

        Returns:
            Maximum distance between centres of adjacent fasteners in mm (float)

        Note:
            Reference:
            IS 800:2025, cl. 17.2.3.2
            For 'compression_butting' (forces transferred through butting faces) 4.5 d applies for a distance equal to
            1.5 times the width of the member from the butting faces.
        """
        t = min(plate_thicknesses)
        if member_type == 'tension':
            return min(16 * t, 200.0)
        elif member_type == 'compression':
            return min(12 * t, 200.0)
        elif member_type == 'compression_butting':
            return 4.5 * d
        raise ValueError("member_type must be 'tension', 'compression' or 'compression_butting'")

    @staticmethod
    def cl_17_2_3_3_max_spacing_along_edge(outer_plate_thicknesses):
        """Calculate the maximum distance between two consecutive fasteners in a line adjacent and parallel to an edge
        of an outside plate

        Args:
             outer_plate_thicknesses - List of thicknesses in mm of the outside plates (list or tuple)

        Returns:
            Maximum distance in mm (float)

        Note:
            Reference:
            IS 800:2025, cl. 17.2.3.3 : 100 mm + 4t or 200 mm, whichever is less
        """
        t = min(outer_plate_thicknesses)
        return min(100.0 + 4 * t, 200.0)

    @staticmethod
    def cl_17_2_4_2_min_edge_end_dist(d, bolt_hole_type='Standard', edge_type='Sheared or hand flame cut'):
        """Calculate minimum end and edge distance

        Args:
             d - Nominal diameter of fastener in mm (float)
             bolt_hole_type - Either 'Standard' or 'Over-sized' or 'short_slot' or 'long_slot' (str)
             edge_type - 'Sheared or hand flame cut' or any other edge, i.e. 'Rolled, machine flame cut, sawn and planed' (str)

        Returns:
            Minimum edge and end distances from the centre of any hole to the nearest edge of a plate in mm (float)

        Note:
            Reference:
            IS 800:2025, cl. 17.2.4.2 : 1.7 d_0 for sheared or hand flame cut edges, 1.5 d_0 for other edges
            Not implemented: the special measurement of edge distance for slotted and oversize holes (cl. 17.2.4.1).
        """
        d_0 = IS800_2025.cl_17_2_1_bolt_hole_size(d, bolt_hole_type)
        if edge_type == 'Sheared or hand flame cut':
            return 1.7 * d_0
        else:
            return 1.5 * d_0

    @staticmethod
    def cl_17_2_4_3_max_edge_dist(conn_plates_t_fu_fy, corrosive_influences=False):
        """Calculate maximum end and edge distance

        Args:
             conn_plates_t_fu_fy - List of tuples with plate thicknesses in mm, fu in MPa, fy in MPa (list of tuples)
                                example:- [ (12, 410, 250), (10, 440, 300) ]
             corrosive_influences - Whether the members are exposed to corrosive influences or not (Boolean)

        Returns:
            Maximum edge distance to the nearest line of fasteners from an edge of any un-stiffened part in mm (float)

        Note:
            Reference:
            IS 800:2025, cl. 17.2.4.3 : 12 t e, with e = sqrt(250/f_y); 40 mm + 4t in corrosive surroundings
            Assumption (as in the 2007 Osdag code): the plate with the smallest value of t*e governs.
        """
        t_epsilon_considered = conn_plates_t_fu_fy[0][0] * math.sqrt(250 / float(conn_plates_t_fu_fy[0][2]))
        t_min = conn_plates_t_fu_fy[0][0]
        for plate in conn_plates_t_fu_fy:
            t = plate[0]
            f_y = plate[2]
            if f_y > 0:
                epsilon = math.sqrt(250 / f_y)
                if t * epsilon <= t_epsilon_considered:
                    t_epsilon_considered = t * epsilon
                if t < t_min:
                    t_min = t

        if corrosive_influences is True:
            return 40.0 + (4 * t_min)
        else:
            return 12 * t_epsilon_considered

    # -------------------------------------------------------------
    #   17.3 Bearing Type Bolts
    # -------------------------------------------------------------

    @staticmethod
    def cl_17_3_2_bolt_design_strength(V_dsb, V_dpb):
        """Calculate design strength of bearing type bolt

        Args:
            V_dsb - Design shear strength of bearing bolt in N (float)
            V_dpb - Design bearing strength of bolt on the plate in N (float)

        Returns:
            V_db - Design strength of bearing bolt in N (float)

        Note:
            Reference:
            IS 800:2025, cl 17.3.2
        """
        V_db = min(V_dsb, V_dpb)
        return V_db

    @staticmethod
    def cl_17_3_3_bolt_shear_capacity(f_ub, A_nb, A_sb, n_n, n_s=0, safety_factor_parameter=None):
        """Calculate design shear strength of bearing bolt

        Args:
            f_ub - Ultimate tensile strength of the bolt in MPa (float)
            A_nb - Net shear area of the bolt at threads in sq. mm  (float)
            A_sb - Nominal plain shank area of the bolt in sq. mm  (float)
            n_n - Number of shear planes with threads intercepting the shear plane (int)
            n_s -  Number of shear planes without threads intercepting the shear plane (int)
            safety_factor_parameter - Either 'field' or 'shop' key of Table 5; shop is used when None (str)

        Returns:
            V_dsb - Design shear strength of bearing bolt in N (float)

        Note:
            Reference:
            IS 800:2025,  cl 17.3.3 (formula unchanged)
            The 2007 Osdag code ignored safety_factor_parameter and always used the shop value; here it is used.
        """
        if safety_factor_parameter is None:
            safety_factor_parameter = KEY_DP_FAB_SHOP
        V_nsb = f_ub / math.sqrt(3) * (n_n * A_nb + n_s * A_sb)
        gamma_mb = IS800_2025.cl_12_4_1_Table_5['gamma_mb'][safety_factor_parameter]
        V_dsb = V_nsb / gamma_mb
        return V_dsb

    @staticmethod
    def cl_17_3_3_1_bolt_long_joint(d, l_j):
        """Calculate reduction factor for long joints.

        Args:
            l_j = Length of joint of a splice or end connection as defined in cl. 17.3.3.1 (float)
            d = Nominal diameter of the fastener (float)

        Returns:
            beta_lj  = Reduction factor for long joints (float)

        Note:
            Reference:
            IS 800:2025,  cl 17.3.3.1
            beta_lj = 1.075 - 0.005 l_j / d, limited to 0.75 <= beta_lj <= 1.0, applies when l_j > 15 d
        """
        beta_lj = 1.075 - 0.005 * l_j / d
        if beta_lj <= 0.75:
            beta_lj = 0.75
        elif beta_lj >= 1.0:
            beta_lj = 1.0
        if l_j >= 15.0 * d:
            return beta_lj
        else:
            return 1.0

    @staticmethod
    def cl_17_3_3_2_bolt_large_grip(d, l_g, l_j=0.0):
        """Calculate reduction factor for large grip lengths.

        Args:
            l_g = Grip length equal to the total thickness of the connected plates as defined in cl. 17.3.3.2 (float)
            d = Nominal diameter of the fastener (float)
            l_j = Length of joint, to apply the upper limit beta_lj (float)

        Returns:
            beta_lg = Reduction factor for large grip lengths (float) if applicable

        Note:
            Reference:
            IS 800:2025,  cl 17.3.3.2
            beta_lg = 8 / (3 + l_g/d) when l_g > 5 d; it shall not be more than beta_lj; l_g shall in no case exceed 8 d
            (use cl_17_3_3_2_grip_length_ok to check the last condition).
        """
        beta_lg = 8.0 / (3.0 + l_g / d)
        if l_j != 0.0:
            beta_lj = IS800_2025.cl_17_3_3_1_bolt_long_joint(d, l_j)
            if beta_lg >= beta_lj:
                beta_lg = beta_lj
        if l_g <= 5.0 * d:
            beta_lg = 1.0
        return round(beta_lg, 2)

    @staticmethod
    def cl_17_3_3_2_grip_length_ok(d, l_g):
        """Check that the grip length does not exceed 8 d (cl. 17.3.3.2)

        Args:
            d = Nominal diameter of the fastener (float)
            l_g = Grip length in mm (float)

        Returns:
            True if l_g <= 8 d (bool)
        """
        return l_g <= 8.0 * d

    @staticmethod
    def cl_17_3_3_3_packing_plates(t=0.0):
        """Calculate reduction factor for packing plates.

        Args:
            t = thickness of the thickest packing plate, in mm

        Returns:
            beta_pk = Reduction factor for packing plates (float) if applicable

        Note:
            Reference:
            IS 800:2025,  cl 17.3.3.3
        """
        if t > 6.0:
            beta_pk = (1.0 - 0.0125 * t)
        else:
            beta_pk = 1.0
        return beta_pk

    @staticmethod
    def cl_17_3_4_bolt_bearing_capacity(f_u, f_ub, t, d, e, p, bolt_hole_type='Standard',
                                        safety_factor_parameter=KEY_DP_FAB_FIELD, round_k_b=True):
        """Calculate design bearing strength of a bolt on any plate.

        Args:
            f_u     - Ultimate tensile strength of the plate in MPa (float)
            f_ub    - Ultimate tensile strength of the bolt in MPa (float)
            t       - Summation of thicknesses of the connected plates in mm as defined in cl. 17.3.4 (float)
            d       - Diameter of the bolt in mm (float)
            e       - End distance of the fastener along bearing direction in mm (float)
            p       - Pitch distance of the fastener along bearing direction in mm (float)
            bolt_hole_type - Either 'Standard' or 'Over-sized' or 'short_slot' or 'long_slot' (str)
            safety_factor_parameter - Either 'Field' or 'Shop' (str)
            round_k_b - round k_b to 2 decimals as the 2007 Osdag code does; use False for the exact value (bool)

        Returns:
            V_dpb - Design bearing strength of bearing bolt in N (float)

        Note:
            Reference:
            IS 800:2025,  cl 17.3.4 (formula unchanged)
            k_b = smaller of e/(3 d_0), p/(3 d_0) - 0.25, f_ub/f_u, 1.0;  V_npb = 2.5 k_b d t f_u
            Oversize and short slotted holes : 0.7;  long slotted holes : 0.5
        """
        d_0 = IS800_2025.cl_17_2_1_bolt_hole_size(d, bolt_hole_type)

        if p > 0.0:
            k_b = min(e / (3.0 * d_0), p / (3.0 * d_0) - 0.25, f_ub / f_u, 1.0)
        else:
            k_b = min(e / (3.0 * d_0), f_ub / f_u, 1.0)  # calculate k_b when there is no pitch (p = 0)

        if round_k_b:
            k_b = round(k_b, 2)
        V_npb = 2.5 * k_b * d * t * f_u
        gamma_mb = IS800_2025.cl_12_4_1_Table_5['gamma_mb'][safety_factor_parameter]
        V_dpb = V_npb / gamma_mb

        if bolt_hole_type == 'Over-sized' or bolt_hole_type == 'short_slot':
            V_dpb *= 0.7
        elif bolt_hole_type == 'long_slot':
            V_dpb *= 0.5

        return V_dpb

    @staticmethod
    def cl_17_3_5_bearing_bolt_tension_resistance(f_ub, f_yb, A_sb, A_n, safety_factor_parameter=KEY_DP_FAB_FIELD):
        """Calculate design tensile strength of bearing bolt

        Args:
            f_ub - Ultimate tensile strength of the bolt in MPa (float)
            f_yb - Yield strength of the bolt in MPa (float)
            A_sb - Shank area of bolt in sq. mm  (float)
            A_n - Net tensile stress area of the bolts as per IS 1367 in sq. mm  (float)

        Returns:
            T_db - Design tensile strength of bearing bolt in N (float)

        Note:
            Reference:
            IS 800:2025,  cl 17.3.5 : T_nb = 0.9 f_ub A_n <= f_yb A_sb (gamma_mb / gamma_m0);  T_db = T_nb / gamma_mb
        """
        gamma_mb = IS800_2025.cl_12_4_1_Table_5['gamma_mb'][safety_factor_parameter]
        gamma_m0 = IS800_2025.cl_12_4_1_Table_5['gamma_m0']['yielding']
        T_nb = min(0.90 * f_ub * A_n, f_yb * A_sb * gamma_mb / gamma_m0)
        return T_nb / gamma_mb

    @staticmethod
    def cl_17_3_6_bearing_bolt_combined_shear_and_tension(V_sb, V_db, T_b, T_db):
        """Check for bolt subjected to combined shear and tension

        Args:
            V_sb - factored shear force acting on the bolt,
            V_db - design shear capacity,
            T_b - factored tensile force acting on the bolt,
            T_db - design tension capacity.

        Returns:
            (V_sb/V_db)^2 + (T_b/T_db)^2, which shall not exceed 1.0

        Note:
            Reference:
            IS 800:2025,  cl 17.3.6
        """
        return (V_sb / V_db) ** 2 + (T_b / T_db) ** 2

    # -------------------------------------------------------------
    #   17.4 Friction Grip Type Bolting
    # -------------------------------------------------------------

    @staticmethod
    def cl_17_4_3_bolt_slip_resistance(f_ub, A_nb, n_e, mu_f, bolt_hole_type='Standard', slip_resistance='ultimate_load'):
        """Calculate design shear strength of friction grip bolt as governed by slip

        Args:
            f_ub - Ultimate tensile strength of the bolt in MPa (float)
            A_nb - Net area of the bolt at threads in sq. mm  (float)
            n_e - Number of  effective interfaces offering  frictional resistance to slip (int)
            mu_f - coefficient of friction (slip factor) as specified in Table 20
            bolt_hole_type - 'Standard', 'Over-sized', 'short_slot', 'long_slot' (loaded perpendicular to the slot)
                             or 'long_slot_parallel' (loaded parallel to the slot) (str)
            slip_resistance - whether slip resistance is required at service load or ultimate load
                              Either 'service_load' or 'ultimate_load' (str)

        Returns:
            V_dsf - Design shear strength of friction grip bolt as governed by slip in N (float), K_h, gamma_mf

        Note:
            Reference:
            IS 800:2025,  cl 17.4.3 - formula and constants unchanged
            V_nsf = mu_f n_e K_h F_0,  F_0 = A_nb (0.70 f_ub),  mu_f <= 0.55,  gamma_mf = 1.10 (service) or 1.25 (ultimate)
            K_h = 1.0 (clearance hole), 0.85 (oversize, short slot, long slot perpendicular), 0.7 (long slot parallel)
        """
        f_0 = 0.70 * f_ub
        F_0 = A_nb * f_0
        if slip_resistance == 'service_load':
            gamma_mf = 1.10
        else:
            gamma_mf = 1.25
        if bolt_hole_type == 'Standard':
            K_h = 1.0
        elif bolt_hole_type in ('Over-sized', 'short_slot', 'long_slot'):
            K_h = 0.85
        elif bolt_hole_type == 'long_slot_parallel':
            K_h = 0.7
        else:
            raise ValueError("Unknown bolt_hole_type: {}".format(bolt_hole_type))
        if mu_f >= 0.55:
            mu_f = 0.55
        V_nsf = mu_f * n_e * K_h * F_0
        V_dsf = V_nsf / gamma_mf
        return V_dsf, K_h, gamma_mf

    # Table 20 Typical Average Values for Coefficient of Friction, mu_f (list) - unchanged from IS 800:2007
    cl_17_4_3_Table_20 = [0.20, 0.50, 0.10, 0.25, 0.30, 0.52, 0.30, 0.30, 0.50, 0.33, 0.48, 0.1]

    @staticmethod
    def cl_17_4_5_friction_bolt_tension_resistance(f_ub, f_yb, A_sb, A_n, safety_factor_parameter=KEY_DP_FAB_FIELD):
        """Calculate design tensile strength of friction grip bolt

        Args:
            f_ub - Ultimate tensile strength of the bolt in MPa (float)
            f_yb - Yield strength of the bolt in MPa (float)
            A_sb - Shank area of bolt in sq. mm  (float)
            A_n - Net tensile stress area of the bolts as per IS 1367 in sq. mm  (float)

        Returns:
            T_df - Design tensile strength of friction grip bolt in N (float)

        Note:
            Reference:
            IS 800:2025,  cl 17.4.5 : T_nf = 0.9 f_ub A_n <= f_yb A_sb (gamma_m1 / gamma_m0);  T_df = T_nf / gamma_mf
        """
        gamma_mf = IS800_2025.cl_12_4_1_Table_5['gamma_mf'][safety_factor_parameter]
        gamma_m0 = IS800_2025.cl_12_4_1_Table_5['gamma_m0']['yielding']
        gamma_m1 = IS800_2025.cl_12_4_1_Table_5['gamma_m1']['ultimate_stress']

        T_nf = min(0.9 * f_ub * A_n, f_yb * A_sb * gamma_m1 / gamma_m0)
        return T_nf / gamma_mf

    @staticmethod
    def cl_17_4_6_friction_bolt_combined_shear_and_tension(V_sf, V_df, T_f, T_df):
        """Calculate combined shear and tension of friction grip bolt

        Args:
            V_sf - applied factored shear at design load
            V_df - design shear strength
            T_f - externally applied factored tension at design load
            T_df - design tension strength

        Returns:
            (V_sf/V_df)^2 + (T_f/T_df)^2, which shall not exceed 1.0

        Note:
            Reference:
            IS 800:2025,  cl 17.4.6
        """
        return (V_sf / V_df) ** 2 + (T_f / T_df) ** 2

    @staticmethod
    def cl_17_4_7_bolt_prying_force(T_e, l_v, f_o, b_e, t, f_y, end_dist, pre_tensioned='', eta=1.5):
        """Calculate prying force of friction grip bolt

        Args:
            T_e - tension in the bolt, N (2 T_e is the force in the 2 bolts on either side of the web/plate)
            l_v - distance from the bolt centre line to the toe of the fillet weld or to half the root radius for a
                  rolled section, mm
            f_o - proof stress in consistent units, N/mm^2
            b_e - effective width of flange per pair of bolts, mm
            t - thickness of the end plate, mm
            f_y - yield stress of the end plate, N/mm^2
            end_dist - end distance, mm
            pre_tensioned - 'Pre-tensioned' for beta = 1, otherwise beta = 2 (str)
            eta - 1.5

        Returns:
            Prying force Q in N (float)

        Note:
            Reference:
            IS 800:2025,  cl 17.4.7 (formula unchanged)
            Q = (l_v / (2 l_e)) [ T_e - beta eta f_o b_e t^4 / (27 l_e l_v^2) ],  l_e = min(end distance, 1.1 t sqrt(beta f_o / f_y))
            All calculations are in N-mm.
        """
        if pre_tensioned == 'Pre-tensioned':
            beta = 1
        else:
            beta = 2

        le_1 = end_dist
        le_2 = (1.1 * t) * math.sqrt((beta * f_o) / f_y)
        l_e = min(le_1, le_2)

        Q = (l_v / (2 * l_e)) * (T_e - ((beta * eta * f_o * b_e * t ** 4) / (27 * l_e * l_v ** 2)))  # N

        if Q < 0:
            Q = 0.0

        return round(Q, 2)  # N

    # -------------------------------------------------------------
    #   17.5 Welds and Welding
    # -------------------------------------------------------------

    @staticmethod
    def cl_17_5_2_3_min_weld_size(part1_thickness, part2_thickness):
        """Calculate minimum size of fillet weld as per Table 21 of IS 800:2025

        Args:
            part1_thickness - Thickness of either plate element being welded in mm (float)
            part2_thickness - Thickness of other plate element being welded in mm (float)

        Returns:
            min_weld_size - Minimum size of first run or of a single run fillet weld in mm (float)

        Note:
            Reference:
            IS 800:2025, Table 21 (Cl 17.5.2.3) - values unchanged from IS 800:2007
            Above 32 mm the minimum size is 10 mm (8 mm for the first run); Note 2 asks for special precautions above 50 mm.
        """
        thicker_part_thickness = max(part1_thickness, part2_thickness)
        thinner_part_thickness = min(part1_thickness, part2_thickness)

        if thicker_part_thickness <= 10.0:
            min_weld_size = 3
        elif thicker_part_thickness <= 20.0:
            min_weld_size = 5
        elif thicker_part_thickness <= 32.0:
            min_weld_size = 6
        else:
            min_weld_size = 10
        if min_weld_size > thinner_part_thickness:  # Note 1 of Table 21
            min_weld_size = thinner_part_thickness
        return min_weld_size

    @staticmethod
    def cl_17_5_3_1_max_weld_throat_thickness(part1_thickness, part2_thickness, special_circumstance=False):
        """Calculate maximum effective throat thickness of fillet weld

        Args:
            part1_thickness - Thickness of either plate element being welded in mm (float)
            part2_thickness - Thickness of other plate element being welded in mm (float)
            special_circumstance - (Boolean)

        Returns:
            maximum effective throat thickness of fillet weld in mm (float)

        Note:
            Reference:
            IS 800:2025,  cl 17.5.3.1 : 0.7 t, or 1.0 t under special circumstances, t = thinner plate
        """
        if special_circumstance is True:
            return min(part1_thickness, part2_thickness)
        else:
            return 0.7 * min(part1_thickness, part2_thickness)

    @staticmethod
    def cl_17_5_3_2_factor_for_throat_thickness(fusion_face_angle=90):
        """Constant K of Table 22 for the angle between fusion faces

        Args:
            fusion_face_angle - Angle between fusion faces in degrees (int)

        Returns:
            K (float), or None if the angle is outside 60 - 120 degrees

        Note:
            Reference:
            IS 800:2025, Table 22 (Cl 17.5.3.2) - values unchanged
        """
        table_22 = {'60-90': 0.70, '91-100': 0.65, '101-106': 0.60, '107-113': 0.55, '114-120': 0.50}
        fusion_face_angle = int(round(fusion_face_angle))
        if 60 <= fusion_face_angle <= 90:
            return table_22['60-90']
        elif 91 <= fusion_face_angle <= 100:
            return table_22['91-100']
        elif 101 <= fusion_face_angle <= 106:
            return table_22['101-106']
        elif 107 <= fusion_face_angle <= 113:
            return table_22['107-113']
        elif 114 <= fusion_face_angle <= 120:
            return table_22['114-120']
        return None

    @staticmethod
    def cl_17_5_3_2_fillet_weld_effective_throat_thickness(fillet_size, fusion_face_angle=90):
        """Calculate effective throat thickness of fillet weld for stress calculation

        Args:
            fillet_size - Size of fillet weld in mm (float)
            fusion_face_angle - Angle between fusion faces in degrees (int)

        Returns:
            Effective throat thickness of fillet weld for stress calculation in mm (float)

        Note:
            Reference:
            IS 800:2025,  cl 17.5.3.2 (and cl. 17.5.3.1: not less than 3 mm)
        """
        K = IS800_2025.cl_17_5_3_2_factor_for_throat_thickness(fusion_face_angle)
        return max(round((K * fillet_size), 2), 3)

    @staticmethod
    def cl_17_5_3_2_fillet_weld_effective_throat_thickness_constant(fusion_face_angle=90):
        """Constant K for the effective throat thickness (same as cl_17_5_3_2_factor_for_throat_thickness,
        kept for compatibility with the 2007 module)

        Args:
            fusion_face_angle - Angle between fusion faces in degrees (int)

        Returns:
            K (float)

        Note:
            Reference:
            IS 800:2025,  cl 17.5.3.2
        """
        return IS800_2025.cl_17_5_3_2_factor_for_throat_thickness(fusion_face_angle)

    @staticmethod
    def cl_17_5_3_3_groove_weld_effective_throat_thickness(*args):
        """Calculate effective throat thickness of complete penetration butt welds

        Args:
            *args: Thicknesses of each plate element being welded in mm (tuple of float)

        Returns:
            Effective throat thickness of CJP butt weld in mm (float)

        Note:
            Reference:
            IS 800:2025,  cl 17.5.3.3 : thickness of the thinner part joined
        """
        return min(*args)

    @staticmethod
    def cl_17_5_4_1_fillet_weld_effective_length(fillet_size, available_length):
        """Calculate effective length of fillet weld from available length to weld in practice

        Args:
            fillet_size - Size of fillet weld in mm (float)
            available_length - Available length in mm to weld the plates in practice (float)

        Returns:
            Effective length of fillet weld in mm (float)

        Note:
            Reference:
            IS 800:2025,  cl 17.5.4.1 : actual length = effective length + 2 x size, and not less than 4 x size
        """
        if available_length <= 4 * fillet_size:
            effective_length = 0
        else:
            effective_length = available_length - 2 * fillet_size
        return effective_length

    @staticmethod
    def cl_17_5_7_1_1_fillet_weld_design_stress(ultimate_stresses, fabrication=KEY_DP_FAB_SHOP):
        """Calculate the design strength of fillet weld

        Args:
            ultimate_stresses - Ultimate stresses of weld and parent metal in MPa (list or tuple)
            fabrication - Either 'shop' or 'field' key of Table 5 (str)

        Returns:
            Design strength of fillet weld in MPa (float)

        Note:
            Reference:
            IS 800:2025,  cl 17.5.7.1.1 : f_wd = (f_u / sqrt(3)) / gamma_mw
        """
        f_u = min(ultimate_stresses)
        f_wn = (f_u / math.sqrt(3))
        gamma_mw = IS800_2025.cl_12_4_1_Table_5['gamma_mw'][fabrication]
        f_wd = f_wn / gamma_mw
        return f_wd

    @staticmethod
    def cl_17_5_7_3_weld_long_joint(l_j, t_t, lower_bound=None):
        """Calculate the reduction factor for long joints in welds

        Args:
            l_j - length of joints in the direction of force transfer in mm (float)
            t_t - throat size of the weld in mm (float)
            lower_bound - optional lower limit of the factor (float). The 2007 Osdag code limited it to 0.6; the draft
                          prints no lower limit, so None is the default.

        Returns:
             Reduction factor, beta_lw for long joints in welds (float)

        Note:
            Reference:
            IS 800:2025,  cl 17.5.7.3 : beta_lw = 1.2 - 0.2 l_j / (150 t_t) <= 1.0, applies when l_j > 150 t_t
        """
        if l_j <= 150 * t_t:
            return 1.0
        beta_lw = 1.2 - ((0.2 * l_j) / (150 * t_t))
        if beta_lw >= 1.0:
            beta_lw = 1.0
        if lower_bound is not None and beta_lw < lower_bound:
            beta_lw = lower_bound
        return beta_lw

    # ==========================================================================
    """    SECTION  18 - 24   SEISMIC, FATIGUE, TESTING, DURABILITY, FIRE, SUSTAINABILITY, FABRICATION   """
    # ==========================================================================
    """     ------------------END------------------     """
