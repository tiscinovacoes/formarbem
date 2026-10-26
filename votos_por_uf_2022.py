#!/usr/bin/env python3
"""Votos válidos de Lula e Bolsonaro por UF no 2º turno de 2022 (TSE, votação por município e zona).

Uso: python votos_por_uf_2022.py [turno]     (padrão: 2)
"""
import io
import sys
import zipfile

import pandas as pd
import requests

URL = "https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_candidato_munzona/votacao_candidato_munzona_2022.zip"
ARQUIVO = "votacao_candidato_munzona_2022_BR.csv"  # presidente; os demais cargos estão nos arquivos por UF
NOMES = {
    "AC": "Acre", "AL": "Alagoas", "AM": "Amazonas", "AP": "Amapá", "BA": "Bahia", "CE": "Ceará",
    "DF": "Distrito Federal", "ES": "Espírito Santo", "GO": "Goiás", "MA": "Maranhão",
    "MG": "Minas Gerais", "MS": "Mato Grosso do Sul", "MT": "Mato Grosso", "PA": "Pará",
    "PB": "Paraíba", "PE": "Pernambuco", "PI": "Piauí", "PR": "Paraná", "RJ": "Rio de Janeiro",
    "RN": "Rio Grande do Norte", "RO": "Rondônia", "RR": "Roraima", "RS": "Rio Grande do Sul",
    "SC": "Santa Catarina", "SE": "Sergipe", "SP": "São Paulo", "TO": "Tocantins", "ZZ": "Exterior",
}


def main(turno: str = "2"):
    r = requests.get(URL, timeout=600)
    r.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        df = pd.read_csv(z.open(ARQUIVO), sep=";", encoding="latin1", dtype=str,
                         usecols=["NR_TURNO", "DS_CARGO", "SG_UF", "NM_URNA_CANDIDATO", "QT_VOTOS_NOMINAIS_VALIDOS"])
    df = df[(df["NR_TURNO"] == turno) & (df["DS_CARGO"] == "Presidente")]  # só presidente
    df["votos"] = pd.to_numeric(df["QT_VOTOS_NOMINAIS_VALIDOS"])
    p = df.pivot_table(index="SG_UF", columns="NM_URNA_CANDIDATO", values="votos", aggfunc="sum").fillna(0).astype(int)

    lula = p["LULA"]
    adv = p.drop(columns="LULA").sum(axis=1) if turno == "1" else p.drop(columns="LULA").iloc[:, 0]
    validos = p.sum(axis=1)
    t = pd.DataFrame({
        "UF": p.index, "Estado": p.index.map(NOMES),
        "Lula (votos)": lula.values, "Lula (%)": (100 * lula / validos).round(2).values,
        "Bolsonaro (votos)": adv.values, "Bolsonaro (%)": (100 * adv / validos).round(2).values,
        "Votos válidos": validos.values,
        "Diferença (Lula - Bolsonaro)": (lula - adv).values,
        "Vencedor": ["Lula" if a > b else "Bolsonaro" for a, b in zip(lula, adv)],
    }).sort_values("Votos válidos", ascending=False, ignore_index=True)
    tot = {"UF": "BR", "Estado": "Total", "Lula (votos)": t["Lula (votos)"].sum(),
           "Bolsonaro (votos)": t["Bolsonaro (votos)"].sum(), "Votos válidos": t["Votos válidos"].sum()}
    tot["Lula (%)"] = round(100 * tot["Lula (votos)"] / tot["Votos válidos"], 2)
    tot["Bolsonaro (%)"] = round(100 * tot["Bolsonaro (votos)"] / tot["Votos válidos"], 2)
    tot["Diferença (Lula - Bolsonaro)"] = tot["Lula (votos)"] - tot["Bolsonaro (votos)"]
    tot["Vencedor"] = "Lula" if tot["Diferença (Lula - Bolsonaro)"] > 0 else "Bolsonaro"
    t = pd.concat([t, pd.DataFrame([tot])], ignore_index=True)

    base = f"dados/votos_por_uf_2022_{turno}t"
    t.to_csv(base + ".csv", index=False, sep=";", decimal=",", encoding="utf-8-sig")
    t.to_excel(base + ".xlsx", sheet_name="Por UF", index=False)
    print(t.to_string(index=False))


if __name__ == "__main__":
    main(*sys.argv[1:])
