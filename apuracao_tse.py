#!/usr/bin/env python3
"""Evolução da apuração presidencial (marcos de 5% em 5% das seções) - 2022 x 2026.

Fontes (TSE, Portal de Dados Abertos / CDN):
  2022: Historico_Totalizacao_Presidente_BR_{1T,2T}_2022.zip
  2026: descobertos via API CKAN do dataset "resultados-2026"
        (ou informados manualmente com --url-2026-1t / --url-2026-2t)

Uso:
  python apuracao_tse.py
  python apuracao_tse.py --url-2026-1t <url.zip> --url-2026-2t <url.zip>
  python apuracao_tse.py --inspecionar          # só lista as colunas de cada CSV
"""
import argparse
import io
import re
import sys
import unicodedata
import zipfile

import pandas as pd
import requests

URLS_2022 = {
    "1T": "https://cdn.tse.jus.br/estatistica/sead/eleicoes/eleicoes2022/Historico_Totalizacao_Presidente_BR_1T_2022.zip",
    "2T": "https://cdn.tse.jus.br/estatistica/sead/eleicoes/eleicoes2022/Historico_Totalizacao_Presidente_BR_2T_2022.zip",
}
CKAN_2026 = "https://dadosabertos.tse.jus.br/api/3/action/package_show?id=resultados-2026"
HEADERS = {"User-Agent": "Mozilla/5.0 (analise-apuracao-tse)"}
MARCOS = list(range(5, 101, 5))

# Candidatos de nome de coluna, em ordem de preferência (após normalização).
COL_CANDIDATO = ["NM_VOTAVEL", "NM_URNA_CANDIDATO", "NM_CANDIDATO", "DS_VOTAVEL"]
COL_VOTOS = ["QT_VOTOS_NOMINAIS_VALIDOS", "QT_VOTOS_NOMINAIS", "QT_VOTOS_TOTALIZADOS", "QT_VOTOS"]
COL_PCT_SECOES = ["PC_SECOES_TOTALIZADAS", "PC_SECOES_APURADAS", "PERC_SECOES_TOTALIZADAS",
                  "PR_SECOES_TOTALIZADAS", "PC_SECOES_TOT"]
COL_SECOES_TOT = ["QT_SECOES_TOTALIZADAS", "QT_SECOES_APURADAS"]
COL_SECOES_UNIV = ["QT_SECOES_TOTAL", "QT_SECOES_UNIVERSO", "QT_SECOES", "QT_TOTAL_SECOES"]
COL_DATA = ["DT_TOTALIZACAO", "DT_ULTIMA_TOTALIZACAO", "DT_GERACAO"]
COL_HORA = ["HH_TOTALIZACAO", "HH_ULTIMA_TOTALIZACAO", "HH_GERACAO"]
NAO_CANDIDATO = re.compile(r"BRANCO|NULO|ANULAD|ABSTEN", re.I)


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Z0-9]+", "_", s.upper()).strip("_")


def achar(cols, candidatos):
    for c in candidatos:
        if c in cols:
            return c
    return None


# ----------------------------------------------------------------- download
def baixar_csvs(url: str) -> pd.DataFrame:
    print(f"Baixando {url}")
    r = requests.get(url, headers=HEADERS, timeout=300)
    r.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        nomes = [n for n in z.namelist() if n.lower().endswith(".csv")]
        if not nomes:
            raise ValueError(f"Nenhum .csv dentro de {url}: {z.namelist()}")
        quadros = []
        for n in nomes:
            with z.open(n) as f:
                quadros.append(pd.read_csv(f, sep=";", encoding="latin1", dtype=str,
                                           na_values=["#NULO#", "#NE#"]))
    df = pd.concat(quadros, ignore_index=True)
    df.columns = [norm(c) for c in df.columns]
    return df


def descobrir_2026() -> dict:
    """Procura no CKAN os ZIPs de histórico de totalização de presidente (BR)."""
    r = requests.get(CKAN_2026, headers=HEADERS, timeout=60)
    r.raise_for_status()
    achados = {}
    for res in r.json()["result"]["resources"]:
        alvo = f"{res.get('name', '')} {res.get('url', '')}".lower()
        if not alvo.strip().endswith(".zip") and ".zip" not in alvo:
            continue
        if "presidente" not in alvo or "totaliza" not in alvo:
            continue
        m = re.search(r"(?<![a-z0-9])([12])t(?![a-z0-9])|([12])\s*º?\s*turno", alvo)
        if not m:
            continue
        turno = f"{m.group(1) or m.group(2)}T"
        achados.setdefault(turno, res["url"])
    return achados


# ----------------------------------------------------------------- análise
def snapshots(df: pd.DataFrame, rotulo: str) -> pd.DataFrame:
    """Uma linha por (candidato, totalização) com votos acumulados e % de seções."""
    cols = set(df.columns)
    c_cand, c_votos = achar(cols, COL_CANDIDATO), achar(cols, COL_VOTOS)
    if not c_cand or not c_votos:
        raise ValueError(f"[{rotulo}] não achei candidato/votos. Colunas: {sorted(cols)}")

    if "DS_CARGO" in cols:
        df = df[df["DS_CARGO"].map(norm).str.contains("PRESIDENTE", na=False)]
    for uf in ("SG_UF", "SG_UE"):
        if uf in cols and (df[uf] == "BR").any():
            df = df[df[uf] == "BR"]
            break

    c_pct, c_tot, c_univ = (achar(cols, COL_PCT_SECOES), achar(cols, COL_SECOES_TOT),
                            achar(cols, COL_SECOES_UNIV))
    c_dt, c_hh = achar(cols, COL_DATA), achar(cols, COL_HORA)

    out = pd.DataFrame({"candidato": df[c_cand].str.strip(),
                        "votos": pd.to_numeric(df[c_votos], errors="coerce")})
    num = lambda s: pd.to_numeric(s.str.replace(",", ".", regex=False), errors="coerce")
    if c_pct:
        out["pct_secoes"] = num(df[c_pct])
    elif c_tot and c_univ:
        out["pct_secoes"] = 100 * num(df[c_tot]) / num(df[c_univ])
    else:
        raise ValueError(f"[{rotulo}] sem coluna de % de seções. Colunas: {sorted(cols)}")

    if c_dt:
        txt = df[c_dt].astype(str) + (" " + df[c_hh].astype(str) if c_hh else "")
        out["horario"] = pd.to_datetime(txt, dayfirst=True, errors="coerce")
    else:
        out["horario"] = pd.NaT
    out["ordem"] = range(len(out))  # desempate: ordem original do arquivo
    out = out[~out["candidato"].str.contains(NAO_CANDIDATO, na=False)].dropna(subset=["votos", "pct_secoes"])
    return out


def marcos_turno(snap: pd.DataFrame, ano: int, turno: str) -> pd.DataFrame:
    # Totalização = (horário, % seções). Soma de candidatos dá o total de válidos.
    snap = snap.copy()
    snap["horario_key"] = snap["horario"].fillna(pd.Timestamp(0))
    chave = ["horario_key", "pct_secoes"]
    tot = snap.groupby(chave).agg(validos=("votos", "sum"), ordem=("ordem", "min")).reset_index()
    tot = tot.sort_values(["horario_key", "pct_secoes", "ordem"]).reset_index(drop=True)
    snap = snap.merge(tot[chave + ["validos"]], on=chave)

    final = tot.iloc[-1]
    fin = snap[(snap.horario_key == final.horario_key) & (snap.pct_secoes == final.pct_secoes)]
    fin = fin.sort_values("votos", ascending=False)
    lula = fin[fin.candidato.str.contains("LULA", case=False)]
    if lula.empty:
        raise ValueError(f"[{ano} {turno}] Lula não encontrado: {fin.candidato.tolist()}")
    lula_nome = lula.candidato.iloc[0]
    adv_nome = fin[fin.candidato != lula_nome].candidato.iloc[0]  # melhor colocado depois de Lula

    linhas = []
    for m in MARCOS:
        i = (tot["pct_secoes"] - m).abs().idxmin()  # primeira ocorrência no empate
        t = tot.loc[i]
        s = snap[(snap.horario_key == t.horario_key) & (snap.pct_secoes == t.pct_secoes)]
        vl = s.loc[s.candidato == lula_nome, "votos"].sum()
        va = s.loc[s.candidato == adv_nome, "votos"].sum()
        linhas.append({
            "Ano": ano, "Turno": turno, "Marco (%)": m,
            "Horário da Totalização": None if t.horario_key == pd.Timestamp(0) else t.horario_key,
            "% Real Apurado": round(t.pct_secoes, 2),
            "Lula (votos)": int(vl), "Lula (%)": round(100 * vl / t.validos, 2),
            "Adversário": adv_nome,
            "Adversário (votos)": int(va), "Adversário (%)": round(100 * va / t.validos, 2),
            "Diferença (Lula - Adv.)": int(vl - va),
        })
    return pd.DataFrame(linhas)


# ----------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url-2026-1t")
    ap.add_argument("--url-2026-2t")
    ap.add_argument("--inspecionar", action="store_true")
    ap.add_argument("--saida", default="evolucao_apuracao_presidencial")
    a = ap.parse_args()

    fontes = {(2022, t): u for t, u in URLS_2022.items()}
    u26 = {"1T": a.url_2026_1t, "2T": a.url_2026_2t}
    if not all(u26.values()):
        try:
            desc = descobrir_2026()
            print("2026 descoberto no CKAN:", desc or "nada encontrado")
            u26 = {t: u26[t] or desc.get(t) for t in u26}
        except Exception as e:  # noqa: BLE001
            print(f"Aviso: falha ao consultar CKAN 2026: {e}", file=sys.stderr)
    for t, u in u26.items():
        if u:
            fontes[(2026, t)] = u
        else:
            print(f"Aviso: sem URL para 2026 {t} (ainda não publicado?). Use --url-2026-{t.lower()}.",
                  file=sys.stderr)

    resultados = []
    for (ano, turno), url in fontes.items():
        try:
            df = baixar_csvs(url)
            if a.inspecionar:
                print(f"\n{ano} {turno}: {len(df)} linhas\nColunas: {list(df.columns)}\n{df.head(3)}")
                continue
            resultados.append(marcos_turno(snapshots(df, f"{ano} {turno}"), ano, turno))
        except Exception as e:  # noqa: BLE001
            print(f"ERRO em {ano} {turno}: {e}", file=sys.stderr)
    if a.inspecionar or not resultados:
        return

    tabela = pd.concat(resultados, ignore_index=True)
    comp = None
    if (tabela.Ano == 2026).any():
        k = ["Turno", "Marco (%)"]
        comp = (tabela[tabela.Ano == 2022].drop(columns="Ano")
                .merge(tabela[tabela.Ano == 2026].drop(columns="Ano"), on=k, suffixes=(" 2022", " 2026")))
    pd.set_option("display.width", 250, "display.max_columns", None)
    print("\n", tabela.to_string(index=False))

    tabela.to_csv(f"{a.saida}.csv", index=False, sep=";", decimal=",", encoding="utf-8-sig")
    with pd.ExcelWriter(f"{a.saida}.xlsx") as xw:
        tabela.to_excel(xw, "Evolução", index=False)
        if comp is not None:
            comp.to_excel(xw, "Comparativo 2022x2026", index=False)
    print(f"\nExportado: {a.saida}.csv / {a.saida}.xlsx")


if __name__ == "__main__":
    main()
