"""Catálogo único de frutas del observatorio (fuente de verdad para todas las vistas).

Cada fruta agrupa sus claves de cultivo en Oro (SNIIM), su nombre en SIAP y su código HS en UN Comtrade.
Cuando una fuente no distingue la fruta (p. ej. HS 080450 agrupa guayaba, mango y mangostán) se indica.
"""
from __future__ import annotations

FRUTAS: dict[str, dict] = {
    "limon": {"sniim": "Limón", "nombre": "Limón", "articulo": "el limón", "claves": ["limon"], "siap": "Limón", "hs": "080550",
              "hs_nota": "HS 080550 agrupa limones y limas"},
    "papaya": {"sniim": "Papaya", "nombre": "Papaya", "articulo": "la papaya", "claves": ["papaya"], "siap": "Papaya", "hs": "080720", "hs_nota": ""},
    "platano": {"sniim": "Plátano", "nombre": "Plátano", "articulo": "el plátano", "claves": ["platano"], "siap": "Plátano", "hs": "080390",
                "hs_nota": "HS 080390 son plátanos frescos o secos, excepto plátano macho"},
    "mango": {"sniim": "Mango", "nombre": "Mango", "articulo": "el mango", "claves": ["mango_ataulfo", "mango_manila"], "siap": "Mango", "hs": "080450",
              "hs_nota": "HS 080450 agrupa guayaba, mango y mangostán"},
    "coco": {"sniim": "Coco", "nombre": "Coco", "articulo": "el coco", "claves": ["coco"], "siap": "Coco fruta", "hs": "080119", "hs_nota": "HS 080119: cocos frescos"},
    "tamarindo": {"sniim": "Tamarindo", "nombre": "Tamarindo", "articulo": "el tamarindo", "claves": ["tamarindo"], "siap": "Tamarindo", "hs": "081340",
                  "hs_nota": "HS 081340 agrupa tamarindo y otras frutas secas"},
    "guayaba": {"sniim": "Guayaba", "nombre": "Guayaba", "articulo": "la guayaba", "claves": ["guayaba"], "siap": "Guayaba", "hs": "080450",
                "hs_nota": "HS 080450 agrupa guayaba, mango y mangostán"},
    "aguacate": {"sniim": "Aguacate", "nombre": "Aguacate", "articulo": "el aguacate", "claves": ["aguacate_hass"], "siap": "Aguacate", "hs": "080440", "hs_nota": ""},
    "sandia": {"sniim": "Sandía", "nombre": "Sandía", "articulo": "la sandía",
               "claves": ["sandia", "sandia_blanca", "sandia_jubilee", "sandia_peacock", "sandia_negra", "sandia_rayada", "sandia_sangria"],
               "siap": "Sandía", "hs": "080711", "hs_nota": ""},
    "guanabana": {"sniim": "Guanabana", "nombre": "Guanábana", "articulo": "la guanábana", "claves": ["guanabana"], "siap": "Guanábana", "hs": None,
                  "hs_nota": "UN Comtrade no tiene un código HS propio para guanábana"},
}

CLAVE_A_FRUTA = {clave: f for f, d in FRUTAS.items() for clave in d["claves"]}


def fruta_de(cultivo: str) -> str:
    """Clave de fruta del catálogo para una clave de cultivo de Oro (p. ej. 'mango_ataulfo' → 'mango')."""
    return CLAVE_A_FRUTA.get(str(cultivo), str(cultivo))
