import pytest

from kredi.hesap import (
    VERGILER, aylik_taksit, brut_oran, mevduat_getirisi, mevduat_yenileme,
    odeme_plani, reel_faiz, yillik_maliyet,
)


def test_vergisiz_taksit_bilinen_deger():
    # 100.000 TL, aylık %3, 12 ay → 10.046,21 TL
    assert aylik_taksit(100_000, 0.03, 12) == pytest.approx(10_046.21, abs=0.01)


def test_faizsiz_kredi_esit_bolunur():
    assert aylik_taksit(12_000, 0.0, 12) == pytest.approx(1_000)


def test_vergiler_brut_orani_artirir():
    v = VERGILER["ihtiyac"]
    assert brut_oran(0.03, **v) == pytest.approx(0.039)
    assert aylik_taksit(100_000, 0.03, 12, **v) > aylik_taksit(100_000, 0.03, 12)


def test_plan_anaparayi_tam_kapatir():
    plan = odeme_plani(250_000, 0.0289, 36, **VERGILER["ihtiyac"])
    assert len(plan) == 36
    assert sum(t.anapara for t in plan) == pytest.approx(250_000)
    assert plan[-1].kalan == pytest.approx(0, abs=1e-6)


def test_plan_taksit_bilesenleri_tutarli():
    for t in odeme_plani(100_000, 0.03, 24, **VERGILER["tasit"]):
        assert t.anapara + t.faiz + t.kkdf + t.bsmv == pytest.approx(t.taksit)


def test_faiz_payi_zamanla_azalir():
    plan = odeme_plani(100_000, 0.03, 12)
    faizler = [t.faiz for t in plan]
    assert faizler == sorted(faizler, reverse=True)


def test_yillik_maliyet_bilesik():
    assert yillik_maliyet(0.03) == pytest.approx(1.03 ** 12 - 1)


def test_mevduat_basit_faiz_ve_stopaj():
    # 100.000 TL, yıllık %45, 32 gün, %17,5 stopaj
    assert mevduat_getirisi(100_000, 0.45, 32, 0.175) == pytest.approx(3_254.79, abs=0.01)


def test_mevduat_yenileme_bilesik_buyur():
    tek = 100_000 + mevduat_getirisi(100_000, 0.40, 365)
    yenilenen = mevduat_yenileme(100_000, 0.40, 30, 12)
    assert yenilenen > tek * 0.99


def test_reel_faiz_fisher():
    assert reel_faiz(0.50, 0.35) == pytest.approx(0.1111, abs=1e-4)
    assert reel_faiz(0.30, 0.35) < 0


def test_gecersiz_girdi():
    with pytest.raises(ValueError):
        aylik_taksit(0, 0.03, 12)
