import pandas as pd

class Cruncher:
    def __init__(self, df1, df2):

        with open('namefix.txt', 'r') as f:
            team_names = [line.strip().split(':') for line in f.readlines()]

        name_fix = {k:v for k,v in iter(team_names)}

        df1['team'] = df1.team.apply(lambda x: name_fix[x]
                                             if x in name_fix.keys() else x)
        df2['team'] = df2.team.apply(lambda x: name_fix[x]
                                             if x in name_fix.keys() else x)

        # Discard teams not on both data frames
        teams = set(df1.team.tolist()).intersection(set(df2.team.tolist()))
        df1 = df1.loc[df1.team.isin(teams)]
        df2 = df2.loc[df2.team.isin(teams)]

        # Make sure games are in tact
        df1 = df1.loc[df1.index.value_counts()==2].reset_index(drop=True)
        df2 = df2.loc[df2.index.value_counts()==2].reset_index(drop=True)

        self._df1 = df1
        self._df2 = df2
        self._df = self._df1.merge(self._df2, on=['date', 'team'])

        # throw out second game on double headers
        self._df = self._df.drop_duplicates(subset=['date','team'],
                                            keep='first')
        self._df = self._df.set_index(['date', 'team' ])

    def check_moneyline(self):
        df = self._df.copy()

        y_vals = df.ml_odds_y.tolist()
        y_vals[::2], y_vals[1::2] = y_vals[1::2], y_vals[::2]
        df['y_ml'] = y_vals

        df.ml_odds_x = df.ml_odds_x.astype(float)
        df.y_ml = df.y_ml.astype(float)

        ml_opp = df[['ml_odds_x', 'y_ml']]

        ml_opp['arb'] = (1/ml_opp.ml_odds_x) + (1/ml_opp.y_ml)
        ml_opp = ml_opp.loc[~ml_opp.arb.isnull()]
        print(ml_opp)

    def check_ou(self):
        df = self._df.copy()
        df = df.loc[(df.over_x == df.over_y)]

        # OU is same for both teams in one game, so slice in half
        df = df[::2]
        x_o, x_u = df.over_odds_x, df.under_odds_x
        y_o, y_u = df.over_odds_y, df.under_odds_y
        ou_opp = pd.DataFrame(pd.concat([x_o, y_u, x_u, y_o],
                                        axis=1)).astype(float)
        ou_opp['arb1'] = (1/ou_opp.over_odds_x) + (1/ou_opp.under_odds_y)
        ou_opp['arb2'] = (1/ou_opp.under_odds_x) + (1/ou_opp.over_odds_y)
        print(ou_opp)
