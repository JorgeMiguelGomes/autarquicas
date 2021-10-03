from typing import List
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


def coalition_to_parties(coalition: str) -> List[str]:
    if coalition == "B.E.":
        return ["B.E."]
    coalition = coalition.replace(" - ", "-")
    return coalition.split(".")


def col_rename(col: str) -> str:
    if not "vote" in col:
        return col
    front, back = col.split(".")
    return front+back[0].upper()+back[1:]


def clean(df: pd.DataFrame) -> pd.DataFrame:
    # drop cols with only nans or only 1 unique value
    df = df.drop(columns=['alternateCandidates', 'displayMessage',
                 'hasNoVoting', 'votes.constituenctyCounter'])

    for c in df.columns:
        if len(df[c].value_counts()) == 2:
            if set(df[c].unique()) == set([0, 1]):
                df[c] = df[c].astype(bool)

    df['coalition'] = df.party
    df['parties'] = df.party.apply(coalition_to_parties)
    df['candidatos'] = df.candidatos.apply(proper_name)

    df = df.drop(columns=['party'])

    df = df.rename(mapper=col_rename, axis='columns')
    return df


if __name__ == "__main__":
    dfs = []
    for y in range(2009, 2023, 4):
        dfs.append(pd.read_csv(
            os.path.join(BASE_PATH, 'final_csv',
                         f'autarquicas_{y}_treated.csv')
        ))
    df = pd.concat(dfs)
    df = clean(df)
    df.to_csv(os.path.join(
        BASE_PATH, 'cleaning', 'autarquicas_treated.csv'))
