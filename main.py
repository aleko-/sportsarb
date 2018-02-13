from crawler import Browser, Cloudbet, Nitrogen, Sportsbet, Betcoin
from cruncher import Cruncher

pd.set_option('display.max_rows', None)

def refresh(bot1, bot2):
    bot1.refresh_opps()
    bot2.refresh_opps()

    df1 = bot1.get_dataframe()
    df2 = bot2.get_dataframe()

    return (df1, df2)

def change_sport(bot1, bot2, sport):
    bot1.go_to_sport(sport)
    bot2.go_to_sport(sport)

    bot1.parse(bot1.make_soup())
    bot2.parse(bot2.make_soup())

    df1 = bot1.get_dataframe()
    df2 = bot2.get_dataframe()

    return (df1, df2)

def recalc(df1, df2):
    cruncher = Cruncher(df1=df1, df2=df2)
    cruncher.check_moneyline()
    cruncher.check_ou()

if __name__ == '__main__':
    cloud = Cloudbet()
    cloud.go_to_sport('nba')
    cloud.make_soup()
    cloud.parse()

    nitro = Nitrogen()
    nitro.send_login()
    nitro.go_to_sport('nba')
    nitro.make_soup()
    nitro.parse()

