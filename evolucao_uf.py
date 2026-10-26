#!/usr/bin/env python3
"""Evolução da apuração presidencial por UF (marcos de 5% das seções) para qualquer ano/turno.

Reconstrói a ordem de totalização juntando, por seção eleitoral:
  - detalhe_votacao_secao_<ano>: DT_PRIM_TOT_PARCIAL_HOR_TSE (quando o TSE totalizou a seção)
  - votacao_secao_<ano>_BR:      votos por candidato (votos válidos = todos, exceto branco 95 e nulo 96)
Adversário = candidato nº 22 (Bolsonaro em 2022, Flávio Bolsonaro em 2026).
Validado em 2022 contra o Historico_Totalizacao_Presidente_BR (mesmos horários nos marcos nacionais).

Uso: python evolucao_uf.py <ano> <turno>      ex.: python evolucao_uf.py 2026 1
"""
import io
import sys
import zipfile

import pandas as pd
import requests

BASE = "https://cdn.tse.jus.br/estatistica/sead/odsele"
CHAVE = ["SG_UF", "CD_MUNICIPIO", "NR_ZONA", "NR_SECAO"]
MARCOS = list(range(5, 101, 5))
NAO_VALIDO = {"95", "96"}  # branco, nulo
LULA, ADV = "13", "22"


def ler_presidente(url: str, turno: str, colunas: list, chunk=1_000_000) -> pd.DataFrame:
    """Baixa o ZIP e lê só as linhas de presidente do turno (arquivos têm GBs; leitura em blocos)."""
    r = requests.get(url, timeout=900)
    r.raise_for_status()
    z = zipfile.ZipFile(io.BytesIO(r.content))
    nome = next(n for n in sorted(z.namelist()) if n.endswith("_BRASIL.csv")) \
        if any(n.endswith("_BRASIL.csv") for n in z.namelist()) else next(n for n in z.namelist() if n.endswith("_BR.csv"))
    partes = []
    for ch in pd.read_csv(z.open(nome), sep=";", encoding="latin1", dtype=str,
                          usecols=colunas + ["NR_TURNO", "DS_CARGO"], chunksize=chunk):
        partes.append(ch[(ch["NR_TURNO"] == turno) & (ch["DS_CARGO"].str.upper() == "PRESIDENTE")])
    return pd.concat(partes, ignore_index=True)


def main(ano: str, turno: str):
    det = ler_presidente(f"{BASE}/detalhe_votacao_secao/detalhe_votacao_secao_{ano}.zip", turno,
                         CHAVE + ["DT_PRIM_TOT_PARCIAL_HOR_TSE"])
    vot = ler_presidente(f"{BASE}/votacao_secao/votacao_secao_{ano}_BR.zip", turno,
                         CHAVE + ["NR_VOTAVEL", "QT_VOTOS"])
    vot["QT_VOTOS"] = pd.to_numeric(vot["QT_VOTOS"])
    vot["valido"] = vot["QT_VOTOS"].where(~vot["NR_VOTAVEL"].isin(NAO_VALIDO), 0)
    g = vot.groupby(CHAVE)
    votos = pd.DataFrame({
        "lula": vot[vot["NR_VOTAVEL"] == LULA].groupby(CHAVE)["QT_VOTOS"].sum(),
        "adv": vot[vot["NR_VOTAVEL"] == ADV].groupby(CHAVE)["QT_VOTOS"].sum(),
        "validos": g["valido"].sum(),
    }).fillna(0).reset_index()
    s = det.merge(votos, on=CHAVE, how="left").fillna({"lula": 0, "adv": 0, "validos": 0})
    s["t"] = pd.to_datetime(s["DT_PRIM_TOT_PARCIAL_HOR_TSE"], dayfirst=True)

    linhas = []
    for uf, d in list(s.groupby("SG_UF")) + [("BR", s)]:
        d = d.sort_values("t", kind="stable").reset_index(drop=True)
        d["pct"] = 100 * (d.index + 1) / len(d)
        d[["L", "A", "V"]] = d[["lula", "adv", "validos"]].cumsum()
        for m in MARCOS:
            r = d.loc[(d["pct"] - m).abs().idxmin()]
            linhas.append({"Ano": int(ano), "Turno": f"{turno}T", "UF": uf, "Marco (%)": m,
                           "Horário da Totalização": r.t, "% Real Apurado": round(r.pct, 2),
                           "Lula (votos)": int(r.L), "Adversário (votos)": int(r.A), "Votos válidos": int(r.V)})
    t = pd.DataFrame(linhas)
    base = f"dados/evolucao_uf_{ano}_{turno}t"
    t.to_csv(base + ".csv", index=False, sep=";", encoding="utf-8-sig")
    f = t[(t.UF == "BR") & (t["Marco (%)"] == 100)].iloc[0]
    print(f"{ano} {turno}T: {len(s)} seções -> {base}.csv | BR final: Lula {f['Lula (votos)']:,} "
          f"adv {f['Adversário (votos)']:,} válidos {f['Votos válidos']:,}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
