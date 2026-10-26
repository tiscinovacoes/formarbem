#!/usr/bin/env python3
"""Evolução da apuração presidencial por UF (marcos de 5% das seções), 2022.

Reconstrói a ordem de totalização juntando, por seção eleitoral:
  - detalhe_votacao_secao_2022: DT_PRIM_TOT_PARCIAL_HOR_TSE (quando o TSE totalizou a seção)
  - votacao_secao_2022_BR:      votos de Lula (13) e Bolsonaro (22)
Validado contra o Historico_Totalizacao_Presidente_BR_2T_2022 (mesmos horários nos marcos nacionais).

Uso: python evolucao_por_uf_2022.py [turno]     (padrão: 2)
"""
import io
import sys
import zipfile

import pandas as pd
import requests

BASE = "https://cdn.tse.jus.br/estatistica/sead/odsele"
URL_DET = f"{BASE}/detalhe_votacao_secao/detalhe_votacao_secao_2022.zip"
URL_VOT = f"{BASE}/votacao_secao/votacao_secao_2022_BR.zip"
CHAVE = ["SG_UF", "CD_MUNICIPIO", "NR_ZONA", "NR_SECAO"]
MARCOS = list(range(5, 101, 5))
NOMES = {
    "AC": "Acre", "AL": "Alagoas", "AM": "Amazonas", "AP": "Amapá", "BA": "Bahia", "CE": "Ceará",
    "DF": "Distrito Federal", "ES": "Espírito Santo", "GO": "Goiás", "MA": "Maranhão",
    "MG": "Minas Gerais", "MS": "Mato Grosso do Sul", "MT": "Mato Grosso", "PA": "Pará",
    "PB": "Paraíba", "PE": "Pernambuco", "PI": "Piauí", "PR": "Paraná", "RJ": "Rio de Janeiro",
    "RN": "Rio Grande do Norte", "RO": "Rondônia", "RR": "Roraima", "RS": "Rio Grande do Sul",
    "SC": "Santa Catarina", "SE": "Sergipe", "SP": "São Paulo", "TO": "Tocantins", "ZZ": "Exterior",
}


def ler_presidente(url: str, turno: str, colunas: list, chunk=1_000_000) -> pd.DataFrame:
    """Baixa o ZIP e lê só as linhas de presidente do turno (arquivos têm GBs; leitura em blocos)."""
    r = requests.get(url, timeout=900)
    r.raise_for_status()
    z = zipfile.ZipFile(io.BytesIO(r.content))
    nome = next(n for n in z.namelist() if n.endswith("_BR.csv") or n.endswith("_BRASIL.csv"))
    partes = []
    for ch in pd.read_csv(z.open(nome), sep=";", encoding="latin1", dtype=str,
                          usecols=colunas + ["NR_TURNO", "DS_CARGO"], chunksize=chunk):
        partes.append(ch[(ch["NR_TURNO"] == turno) & (ch["DS_CARGO"].str.upper() == "PRESIDENTE")])
    return pd.concat(partes, ignore_index=True)


def main(turno: str = "2"):
    det = ler_presidente(URL_DET, turno, CHAVE + ["DT_PRIM_TOT_PARCIAL_HOR_TSE"])
    vot = ler_presidente(URL_VOT, turno, CHAVE + ["NR_VOTAVEL", "QT_VOTOS"])
    vot["QT_VOTOS"] = pd.to_numeric(vot["QT_VOTOS"])
    votos = (vot[vot["NR_VOTAVEL"].isin(["13", "22"])]
             .pivot_table(index=CHAVE, columns="NR_VOTAVEL", values="QT_VOTOS", aggfunc="sum")
             .fillna(0).rename(columns={"13": "lula", "22": "bolsonaro"}).reset_index())
    s = det.merge(votos, on=CHAVE, how="left").fillna({"lula": 0, "bolsonaro": 0})
    s["t"] = pd.to_datetime(s["DT_PRIM_TOT_PARCIAL_HOR_TSE"], dayfirst=True)

    linhas = []
    for uf, g in list(s.groupby("SG_UF")) + [("BR", s)]:
        g = g.sort_values("t", kind="stable").reset_index(drop=True)
        g["pct"] = 100 * (g.index + 1) / len(g)
        g["L"], g["B"] = g["lula"].cumsum(), g["bolsonaro"].cumsum()
        for m in MARCOS:
            r = g.loc[(g["pct"] - m).abs().idxmin()]
            val = r.L + r.B
            linhas.append({
                "UF": uf, "Estado": NOMES.get(uf, "Brasil"), "Marco (%)": m,
                "Horário da Totalização": r.t, "% Real Apurado": round(r.pct, 2),
                "Lula (votos)": int(r.L), "Lula (%)": round(100 * r.L / val, 2),
                "Bolsonaro (votos)": int(r.B), "Bolsonaro (%)": round(100 * r.B / val, 2),
                "Diferença (Lula - Bolsonaro)": int(r.L - r.B),
            })
    t = pd.DataFrame(linhas)
    base = f"dados/evolucao_por_uf_2022_{turno}t"
    t.to_csv(base + ".csv", index=False, sep=";", decimal=",", encoding="utf-8-sig")
    t.to_excel(base + ".xlsx", sheet_name="Evolução por UF", index=False)
    print(f"{len(s)} seções, {t['UF'].nunique()} recortes -> {base}.csv/.xlsx")


if __name__ == "__main__":
    main(*sys.argv[1:])
