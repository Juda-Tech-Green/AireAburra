import pandas as pd
import numpy as np



# Constantes de validación
LIMITES_FISICOS = {
    'pm2.5': (0, 200),
    'pm10':  (0, 300),
    'no':(0,250),
    'no2':   (0, 250),
    'nox':(0,250),
    'so2':   (0, 200),
    'co':    (0, 50000),
    'o3':    (0, 200),
    'haire2': (0, 100),
    'haire10': (0, 100),
    'taire2': (5, 50),
    'taire10': (5, 50),
    'tmpr air 10cm':(5,50),
    'p': (0, 100),
    'rglobal': (0, 1500),
    'vviento': (0, 30)
}

def limpiar_serie(serie: pd.Series, nombre_parametro: str) -> pd.Series:
    """
    Recibe una Serie de datos crudos y aplica filtros físicos y estadísticos.
    Devuelve la Serie con los valores anómalos convertidos a NaN.
    """
    serie_clean = serie.copy()
    param_lower = nombre_parametro.lower()

    # 1. LÍMITES FÍSICOS (Hard Limits)
    limites = None
    for key, val in LIMITES_FISICOS.items():
        if key in param_lower:
            limites = val
            break
    
    if limites:
        vmin, vmax = limites
        mask_bad = (serie_clean < vmin) | (serie_clean > vmax)
        if mask_bad.sum() > 0:
            # print(f"   🧹 [Rango] {nombre_parametro}: {mask_bad.sum()} descartados.")
            serie_clean.loc[mask_bad] = np.nan

    # 2. ESTADÍSTICO (Z-Score Móvil)
    # Excluimos variables circulares o muy volátiles
    if 'dviento' not in param_lower and 'pliquida' not in param_lower:
        # Rolling de 30 días
        rolling = serie_clean.rolling(window=30, min_periods=5)
        media = rolling.mean()
        desv = rolling.std()
        
        upper = media + 4 * desv
        lower = media - 4 * desv
        
        mask_zscore = (serie_clean > upper) | (serie_clean < lower)
        
        # Protección para ceros naturales (Radiación noche, Lluvia)
        if 'rglobal' in param_lower:
             mask_zscore = mask_zscore & (serie_clean != 0)

        if mask_zscore.sum() > 0:
            # print(f"   🧹 [Estadístico] {nombre_parametro}: {mask_zscore.sum()} picos anómalos.")
            serie_clean.loc[mask_zscore] = np.nan

    return serie_clean