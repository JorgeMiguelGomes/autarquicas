from typing import List, Dict, Set
import pandas as pd
import json
import os
import re
import time


BASE_PATH = os.path.dirname(os.path.dirname(__file__))


def proper_name(name: str) -> str:
    parts: List[str] = re.split(" |'", name.strip())
    for i, p in enumerate(parts):
        if p == "":
            continue
        if p.lower() in "d,da,das,de,do,dos,e".split(","):
            parts[i] = p.lower()
            continue
        parts[i] = p.capitalize()
    new_name: str = " ".join(parts)
    return re.sub(" +", " ", new_name)


def col_rename(col: str) -> str:
    if not "vote" in col:
        return "candidate" if col == "candidatos" else col
    front, back = col.split(".")
    return front + back[0].upper() + back[1:]


def clean_coalition_name(x: str) -> str:
    x = x.replace("B.E.", "BE")
    x = x.replace("R.I.R.", "RIR")
    x = x.replace(" - ", "-")
    x = re.sub("«|»", "", x)
    return x.upper()


def min_idx(s: str, chars: str, start: int = 0) -> int:
    temp: str = s[start:]
    if not any(d in temp for d in chars):
        return -1
    return start + min(temp.index(d) for d in chars if d in temp)


def clean(df: pd.DataFrame) -> pd.DataFrame:
    # drop cols with only nans or only 1 unique value
    df = df.drop(
        columns=[
            "alternateCandidates",
            "displayMessage",
            "hasNoVoting",
            "votes.constituenctyCounter",
        ]
    )
    # drop cols which with repeated info for old elections
    df = df.drop(columns=["mandates", "presidents"])

    # convert 0/1s to bools
    for c in df.columns:
        if len(df[c].value_counts()) == 2:
            if set(df[c].unique()) == set([0, 1]):
                df[c] = df[c].astype(bool)

    df["candidatos"] = df.candidatos.apply(proper_name)

    # clean party names and break down coalitions
    df.party = df.party.apply(clean_coalition_name)
    unique_parties: Set[str] = set(df.party.unique())

    def coalition_to_parties(coalition: str) -> List[str]:
        if coalition[-1] == ".":
            return [coalition.replace(".", "")]
        if not any(d in coalition for d in ".-/"):
            return [coalition]
        parties: List[str] = []
        idx: int = min_idx(coalition, ".-/")
        while idx >= 0 and idx < len(coalition) and any(d in coalition for d in ".-/"):
            if coalition[:idx] in unique_parties:
                parties.append(coalition[:idx])
                coalition = coalition[idx + 1:]
                idx = 0
            elif coalition[:idx].replace(".", "") in unique_parties:
                parties.append(coalition[:idx])
                coalition = coalition[idx + 1:]
                idx = 0
            idx = min_idx(coalition, ".-/", idx + 1)
        if coalition != "":
            parties.append(coalition)
        parties.sort()
        return parties

    df["coalition"] = df.party
    coalition_lookup: Dict[str, List[str]] = {
        c: coalition_to_parties(c) for c in df.coalition.unique()
    }
    df["parties"] = df.coalition.apply(lambda c: coalition_lookup[c])

    df = df.drop(columns=["party"])

    df = df.rename(mapper=col_rename, axis="columns")
    return df


if __name__ == "__main__":
    dfs = []
    for y in range(2009, 2023, 4):
        dfs.append(
            pd.read_csv(
                os.path.join(BASE_PATH, "final_csv",
                             f"autarquicas_{y}_treated.csv"),
                index_col=0,
            )
        )
    df = pd.concat(dfs)
    df = clean(df)
    df.to_csv(os.path.join(BASE_PATH, "cleaning", "autarquicas_treated.csv"))
