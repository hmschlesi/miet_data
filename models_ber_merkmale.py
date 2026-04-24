from pydantic import BaseModel, Field
from typing import Optional, List

class BaseMerkmalGroup(BaseModel):
    def get_score(self) -> int:
        """Calculates impact based on simple majority rule[cite: 379]."""
        pos_count = sum(1 for k, v in self.model_dump().items() if k.startswith('pos_') and v is True)
        neg_count = sum(1 for k, v in self.model_dump().items() if k.startswith('neg_') and v is True)
        if pos_count > neg_count: return 1
        if neg_count > pos_count: return -1
        return 0

class BadGroup(BaseMerkmalGroup):
    """Merkmalgruppe 1: Bad/WC/Gäste-WC [cite: 402, 404]"""
    # Negative (-)
    neg_kein_handwaschbecken: bool = Field(False, description="No washbasin or only a small one (50x25cm or smaller) [cite: 407-410].")
    neg_wc_ohne_lueftung: bool = Field(False, description="WC without ventilation or exhaust [cite: 411-412].")
    neg_dielenfussboden: bool = Field(False, description="Floorboards in bath not suitable for wet rooms [cite: 413-414].")
    neg_nicht_beheizbar: bool = Field(False, description="Bath not heatable or only wood/coal/electric radiant heater [cite: 415-416, 429].")
    neg_warmwasser_unzureichend: bool = Field(False, description="No central hot water, flow heater, or boiler > 60L [cite: 430-433].")
    neg_bad_ohne_dusche_freistehend: bool = Field(False, description="Bath without separate shower, only freestanding tub in non-modernized bath [cite: 434-436].")
    neg_waende_spritzwasser_ungefliest: bool = Field(False, description="Walls not sufficiently tiled in splash zones [cite: 437-438].")
    neg_bad_wc_ohne_fenster: bool = Field(False, description="Bath with WC has no window (Not for 1973-1990 East) [cite: 439-440].")
    neg_keine_duschmoeglichkeit: bool = Field(False, description="No shower possibility (e.g., no splash protection or shower head holder) [cite: 441-442].")
    neg_kleines_bad_unter_4qm: bool = Field(False, description="Bath smaller than 4m² (Not for 1973-1990 East) [cite: 443-444].")

    # Positive (+)
    pos_doppel_waschbecken: bool = Field(False, description="Very large basin (min 80cm), double basin, or two separate basins [cite: 456-459].")
    pos_hochwertige_ausstattung: bool = Field(False, description="E.g., high-quality sanitary items, high-end bath furniture, corner tub [cite: 460-463].")
    pos_moderne_entlueftung: bool = Field(False, description="Interior bath with modern controlled ventilation (e.g., humidity sensor) [cite: 464-466].")
    pos_zweites_wc_oder_getrennt: bool = Field(False, description="Second WC in apartment or separate bath and WC[cite: 467].")
    pos_bad_ueber_8qm: bool = Field(False, description="At least one bath larger than 8m² .")
    pos_fussbodenheizung: bool = Field(False, description="Underfloor heating in the bathroom [cite: 470-471].")
    pos_wand_boden_hochwertig: bool = Field(False, description="High-quality wall/floor covering (Not for 2016-2022) [cite: 472-474].")
    pos_wandhaengendes_wc: bool = Field(False, description="Wall-hung WC with concealed tank (Not for build after 2002) [cite: 475-478].")
    pos_tuchwaermer: bool = Field(False, description="Towel warmer radiator (Built up to 2001; if electric, all years) [cite: 479-483].")
    pos_separate_dusche: bool = Field(False, description="Additional shower tray or cabin separate from bathtub[cite: 484].")
    pos_bodengleiche_dusche: bool = Field(False, description="Floor-level shower (up to 3cm depth) [cite: 485-486].")

class KuecheGroup(BaseMerkmalGroup):
    """Merkmalgruppe 2: Küche [cite: 445, 487]"""
    # Negative (-)
    neg_kueche_ohne_fenster: bool = Field(False, description="Kitchen without window and sufficient ventilation[cite: 445].")
    neg_keine_kochmoeglichkeit: bool = Field(False, description="No cooking facility or stove without oven[cite: 447].")
    neg_keine_spuele: bool = Field(False, description="No sink provided[cite: 448].")
    neg_warmwasser_unzureichend: bool = Field(False, description="No central hot water, flow heater, or boiler[cite: 449].")
    neg_nicht_beheizbar: bool = Field(False, description="Kitchen not heatable or only wood/coal heating [cite: 450-451].")
    neg_geschirrspueler_nicht_stellbar: bool = Field(False, description="Dishwasher cannot be placed or connected [cite: 452-453].")
    neg_keine_wandfliesen: bool = Field(False, description="No wall tiles or wall protection in work area[cite: 454].")

    # Positive (+)
    pos_boden_hochwertig: bool = Field(False, description="E.g., high-quality tiles, linoleum, laminate, parquet, or terrazzo (Built up to 2009) [cite: 488-493].")
    pos_separate_kueche_gross: bool = Field(False, description="Separate kitchen with at least 14m² area[cite: 494].")
    pos_einbaukueche: bool = Field(False, description="Fitted kitchen with cabinets, stove, and sink [cite: 495-496].")
    pos_ceran_induktion: bool = Field(False, description="Ceran or induction cooktop (Built up to 2001) [cite: 497-498].")
    pos_dunstabzug: bool = Field(False, description="Extractor hood provided[cite: 499].")
    pos_geraete_gestellt: bool = Field(False, description="Refrigerator, freezer, or dishwasher provided[cite: 501].")
    pos_kuechenblock: bool = Field(False, description="Freestanding kitchen island with work surface and cooking/sink[cite: 502].")

class WohnungGroup(BaseMerkmalGroup):
    """Merkmalgruppe 3: Wohnung [cite: 506, 529]"""
    # Negative (-)
    neg_einfachverglasung: bool = Field(False, description="Predominantly single-glazed windows[cite: 507].")
    neg_elektro_unzureichend: bool = Field(False, description="Insufficient electrical installation (no RCD/FI, potential equalization) [cite: 508-509].")
    neg_leitungen_auf_putz: bool = Field(False, description="Majority of electrical or water pipes visible on walls [cite: 510-511].")
    neg_waschmaschine_nicht_stellbar: bool = Field(False, description="Washing machine cannot be placed/connected in bath or kitchen[cite: 512].")
    neg_schlechter_schnitt: bool = Field(False, description="Poor layout (e.g., walk-through rooms) [cite: 513-514].")
    neg_kein_balkon: bool = Field(False, description="No balcony, terrace, loggia, or winter garden[cite: 515].")

    # Positive (+)
    pos_einbauschrank: bool = Field(False, description="Built-in closet or storage room within apartment[cite: 530].")
    pos_grosser_balkon: bool = Field(False, description="Balcony, terrace, loggia, or winter garden >= 4m² [cite: 531-532].")
    pos_fussbodenheizung_ueberwiegend: bool = Field(False, description="Underfloor heating in majority of rooms[cite: 533].")
    pos_aufwaendige_verkleidung: bool = Field(False, description="E.g., stucco or paneling in good condition[cite: 534].")
    pos_rohre_unsichtbar: bool = Field(False, description="Heating pipes mostly invisible (Built up to 1990) [cite: 535-538].")
    pos_rolllaeden: bool = Field(False, description="External shutters/roller blinds[cite: 539].")
    pos_zimmer_ueber_40qm: bool = Field(False, description="At least one living room larger than 40m²[cite: 540].")
    pos_barrierearm: bool = Field(False, description="Threshold-free, barrier-free bathroom, or sufficient movement space [cite: 541-544].")
    pos_boden_hochwertig: bool = Field(False, description="High-quality parquet, stone, or tiles in majority of rooms[cite: 545].")
    pos_modernes_glas: bool = Field(False, description="Thermal or sound insulation glass (Built before 2002).")
    pos_einbruchsicherung: bool = Field(False, description="Additional security for entrance door (e.g., multi-point locking).")

class GebaeudeGroup(BaseMerkmalGroup):
    """Merkmalgruppe 4: Gebäude [cite: 516, 547, 571, 573]"""
    # Negative (-)
    neg_treppenhaus_schlecht: bool = Field(False, description="Entrance/staircase in poor condition [cite: 518-519].")
    neg_kein_abstellraum_extern: bool = Field(False, description="No private storage room outside apartment (e.g., cellar) [cite: 519-520].")
    neg_hauseingang_offen: bool = Field(False, description="House entrance freely accessible from outside[cite: 521].")
    neg_instandhaltung_mangelhaft: bool = Field(False, description="Poor maintenance (e.g., damp masonry, roof/plaster damage) [cite: 522-523].")
    neg_seitenfluegel: bool = Field(False, description="Location in side wing or rear building with dense construction [cite: 524-525].")
    neg_kein_aufzug: bool = Field(False, description="Apartment above 4th floor without elevator (Not for up to 1949)[cite: 526].")
    neg_keine_gegensprechanlage: bool = Field(False, description="No intercom with electric door opener[cite: 527].")
    neg_waermedaemmung_unzureichend: bool = Field(False, description="Insufficient insulation or heating efficiency (Built before 1995)[cite: 572].")
    neg_energieverbrauch_hoch: bool = Field(False, description="Energy consumption > 145 kWh/(m²a)[cite: 576].")

    # Positive (+)
    pos_fahrradraum: bool = Field(False, description="Lockable bike room or secure bike racks on property [cite: 556-557].")
    pos_gemeinschaftsraum: bool = Field(False, description="Additional usable rooms outside apartment (e.g., community room)[cite: 558].")
    pos_repraesentativer_eingang: bool = Field(False, description="High-quality/renovated entrance area (e.g., marble, carpets)[cite: 559].")
    pos_instandhaltung_gut: bool = Field(False, description="Above-average building maintenance (e.g., renewed facade/roof; Built up to 2015) [cite: 560-561].")
    pos_video_gegensprechanlage: bool = Field(False, description="Intercom with video and electric door opener[cite: 562].")
    pos_aufzug_niedrig: bool = Field(False, description="Elevator provided with fewer than 5 upper floors (Not for after 2010)[cite: 563].")
    pos_schwellenfreier_zugang: bool = Field(False, description="Low-threshold access to building and apartment[cite: 564].")
    pos_waermedaemmung_modern: bool = Field(False, description="Additional insulation or modern heating (Since 2009; for older builds)[cite: 574].")
    pos_energieverbrauch_niedrig: bool = Field(False, description="Energy consumption < 120 kWh/(m²a)[cite: 578].")

class WohnumfeldGroup(BaseMerkmalGroup):
    """Merkmalgruppe 5: Wohnumfeld [cite: 584, 588]"""
    # Negative (-)
    neg_vernachlaessigt: bool = Field(False, description="Location in a heavily neglected environment[cite: 585].")
    neg_laermbelastung: bool = Field(False, description="High noise (e.g., main road, airport, industry, gastro) [cite: 586-587].")
    neg_geruchsbelastung: bool = Field(False, description="Particularly high odor pollution[cite: 592].")
    neg_kein_fahrradplatz_grundstueck: bool = Field(False, description="No bicycle parking facility on the property[cite: 593].")

    # Positive (+)
    pos_citylage: bool = Field(False, description="Preferred city location near major shopping/service hubs[cite: 596].")
    pos_besonders_ruhig: bool = Field(False, description="Particularly quiet (e.g., traffic-calmed, near park)[cite: 597].")
    pos_gestaltetes_umfeld: bool = Field(False, description="E.g., playground, benches, good lighting/paving (Built before 2002)[cite: 598].")
    pos_parkplatz_angebot: bool = Field(False, description="Landlord provides sufficient parking spaces nearby[cite: 598].")
    pos_mietergarten: bool = Field(False, description="Garden for sole use or with direct access[cite: 598].")

class MietspiegelEvaluation(BaseModel):
    bad: BadGroup = Field(default_factory=BadGroup)
    kueche: KuecheGroup = Field(default_factory=KuecheGroup)
    wohnung: WohnungGroup = Field(default_factory=WohnungGroup)
    gebaeude: GebaeudeGroup = Field(default_factory=GebaeudeGroup)
    umfeld: WohnumfeldGroup = Field(default_factory=WohnumfeldGroup)

    def calculate_adjustment_percentage(self) -> float:
        """Each group with a majority contributes +/- 20% of the span [cite: 371-377]."""
        groups = [self.bad, self.kueche, self.wohnung, self.gebaeude, self.umfeld]
        return sum(g.get_score() for g in groups) * 0.20