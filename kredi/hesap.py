"""Kredi, mevduat ve reel faiz hesapları.

Türkiye'de bireysel kredilerde faize KKDF ve BSMV eklenir. Taksit, vergiler dahil
"brüt" aylık oranla eşit taksit (annüite) formülüyle hesaplanır:

    r_brüt = r × (1 + KKDF + BSMV)
    taksit = P × r_brüt / (1 − (1 + r_brüt)^−n)

Oranlar ondalık olarak verilir: %3,5 → 0.035.
"""

from dataclasses import dataclass

# Kredi türüne göre varsayılan vergi oranları. Mevzuat değişebilir; kullanmadan önce
# güncel oranları kontrol edin.
VERGILER = {
    "ihtiyac": {"kkdf": 0.15, "bsmv": 0.15},
    "tasit": {"kkdf": 0.15, "bsmv": 0.15},
    "konut": {"kkdf": 0.0, "bsmv": 0.0},
}


@dataclass(frozen=True)
class Taksit:
    ay: int
    taksit: float
    anapara: float
    faiz: float
    kkdf: float
    bsmv: float
    kalan: float


def brut_oran(aylik_faiz: float, kkdf: float = 0.0, bsmv: float = 0.0) -> float:
    """Vergiler dahil aylık maliyet oranı."""
    return aylik_faiz * (1 + kkdf + bsmv)


def aylik_taksit(anapara: float, aylik_faiz: float, vade: int,
                 kkdf: float = 0.0, bsmv: float = 0.0) -> float:
    """Eşit taksitli kredinin aylık taksiti."""
    if anapara <= 0 or vade <= 0:
        raise ValueError("Anapara ve vade pozitif olmalı.")
    r = brut_oran(aylik_faiz, kkdf, bsmv)
    if r == 0:
        return anapara / vade
    return anapara * r / (1 - (1 + r) ** -vade)


def odeme_plani(anapara: float, aylik_faiz: float, vade: int,
                kkdf: float = 0.0, bsmv: float = 0.0) -> list[Taksit]:
    """Ay ay ödeme planı: her taksitin anapara, faiz ve vergi payı."""
    taksit = aylik_taksit(anapara, aylik_faiz, vade, kkdf, bsmv)
    kalan = anapara
    plan = []
    for ay in range(1, vade + 1):
        faiz = kalan * aylik_faiz
        anapara_payi = taksit - faiz * (1 + kkdf + bsmv)
        if ay == vade:  # yuvarlama artığını son taksitte kapat
            anapara_payi = kalan
        kalan -= anapara_payi
        plan.append(Taksit(ay, taksit, anapara_payi, faiz, faiz * kkdf, faiz * bsmv, max(kalan, 0.0)))
    return plan


def yillik_maliyet(aylik_faiz: float, kkdf: float = 0.0, bsmv: float = 0.0) -> float:
    """Yıllık bileşik maliyet oranı: (1 + r_brüt)^12 − 1."""
    return (1 + brut_oran(aylik_faiz, kkdf, bsmv)) ** 12 - 1


def mevduat_getirisi(anapara: float, yillik_faiz: float, gun: int,
                     stopaj: float = 0.0) -> float:
    """Vadeli mevduatın vade sonundaki net faizi (basit faiz, 365 gün esası)."""
    return anapara * yillik_faiz * gun / 365 * (1 - stopaj)


def mevduat_yenileme(anapara: float, yillik_faiz: float, gun: int,
                     donem: int, stopaj: float = 0.0) -> float:
    """Mevduat her vade sonunda faiziyle yenilenirse `donem` vade sonraki bakiye."""
    bakiye = anapara
    for _ in range(donem):
        bakiye += mevduat_getirisi(bakiye, yillik_faiz, gun, stopaj)
    return bakiye


def reel_faiz(nominal: float, enflasyon: float) -> float:
    """Fisher denklemi: (1 + i) / (1 + π) − 1."""
    return (1 + nominal) / (1 + enflasyon) - 1
