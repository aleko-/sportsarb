# sportsarb

Code will successfully identify arbitrage opportunities from supported websites. Future work should focus on automating the interactions between cralwers, multiprocessing so that cralwers can spawn simaltaneously, and adding support for more sports and websites.

main.py

## usage
----
    >>> from crawler import Browser, Cloudbet, Nitrogen, Sportsbet, Betcoin
    >>> from cruncher import Cruncher
    >>> import main
    >>>
    >>> cloud = Cloudbet()
    >>> cloud.go_to_sport('nba')
    >>> cloud.make_soup()
    >>> cloud.parse()
    >>> df1 = cloud.get_dataframe()
    >>>
    >>> nitro = Nitrogen()
    >>> nitro.send_login()
    >>> nitro.go_to_sport('nba')
    >>> nitro.make_soup()
    >>> nitro.parse()
    >>> df2 = nitro.get_dataframe()
    >>>
    >>> main.calc(df1, df2)
                                           ml_odds_x   y_ml       arb
    date       team
    2018-02-13 Toronto Raptors              1.32  3.708  1.027263
               Miami Heat                   3.72  1.304  1.035688
               Minnesota Timberwolves       2.28  1.680  1.033835
               Houston Rockets              1.69  2.264  1.033412
               Milwaukee Bucks              1.34  3.520  1.030360
               Atlanta Hawks                3.55  1.329  1.034136
                                       over_odds_x  under_odds_y  under_odds_x  \
    date       team
    2018-02-13 Toronto Raptors                1.95          1.93          1.95
               Minnesota Timberwolves         1.95          1.93          1.95
               Milwaukee Bucks                1.95          1.93          1.95

                                       over_odds_y      arb1      arb2
    date       team
    2018-02-13 Toronto Raptors                1.93  1.030955  1.030955
               Minnesota Timberwolves         1.93  1.030955  1.030955
               Milwaukee Bucks                1.93  1.030955  1.030955

----

An arbitrage opportunity is found when a the value in an 'arb' field is less than 1.

* *ml\_odds_x*  - moneyline odds on website 1

* *y_ml*  - moneyline odds on website 2

Over/Under columns are self explanatory. Opposing teams are omitted from the over/under dataframe to reduce redundancy.
