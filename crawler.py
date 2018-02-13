from selenium import webdriver
from iteration_utilities import deepflatten
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import time

class Browser:
    def __init__(self, base, open_base=0):

        agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:55.0) Gecko/20100101 Firefox/55.0"
        profile = webdriver.FirefoxProfile()
        profile.set_preference("general.useragent.override", agent)
        self._driver = webdriver.Firefox(profile)

        self._soup = None

        if open_base:
            self._driver.get(base)
            self.wait(open_base)

    def wait(self, s):
        """
        Pause to allow HTML to render
        """
        time.sleep(s)

    def login(self, user, pw, xstart, xuser, xlogin, xpw, xsub):
        """
        Log in to site
        """
        self._driver.find_element_by_xpath(xstart).click()
        self.wait(2)
        self._driver.find_element_by_xpath(xuser).send_keys(user)
        self._driver.find_element_by_xpath(xlogin).click()
        self._driver.find_element_by_xpath(xpw).send_keys(pw)
        self._driver.find_element_by_xpath(xsub).click()

    def make_soup(self):
        page = self._driver.find_element_by_xpath("//*")
        html = page.get_attribute("outerHTML")
        self._soup = BeautifulSoup(html, "html.parser")

    def go_to_page(self, page):
        path = self._base + page
        self._driver.get(path)
        self.wait(5)

    def refresh_opps(self):
        """
        Refresh page and gather updated stats
        """
        if self._refresh_needed:
            self._driver.refresh()
            self.wait(5)
        else:
            self.make_soup()
            self.parse()

    def change_sport(self, sport):
        self.go_to_sport(sport)

class Nitrogen(Browser):
    def __init__(self):

        with open('passwords.txt', 'r') as f:
            user, pw = f.read().split()

        self._base   = "https://nitrogensports.eu/"
        self._user   = user
        self._pw     = pw
        self._xstart = '//*[@id="modal-welcome-login-button"]'
        self._xuser  = '//*[@id="modal-account-login-username-textbox"]'
        self._xpw    = '//*[@id="modal-account-login-password-textbox"]'
        self._xsub   = '//*[@id="modal-account-login-button"]'
        self._df     = None

        self._refresh_needed = True

        Browser.__init__(self, base=self._base, open_base=8)

    def send_login(self):
        self.login(user=self._user, pw=self._pw, xstart=self._xstart,
                   xuser=self._xuser, xlogin=self._xuser, xpw=self._xpw,
                   xsub=self._xsub)
        self.wait(2)

    def go_to_sport(self, page):
        path = self._base + '/sport/' + page
        self._driver.get(path)
        self.wait(5)

    def parse(self):
        events = [x for x in self._soup.find_all('div', {'class' : 'event'})
                          if 'Betting on hold' not in x.text
                          and 'Nitrogen' not in x.text
                          and 'balance' not in x.text]

        df = pd.DataFrame()
        for event in events:
            match_raw = event.find_all('div', {'class' :
                                               'event-participant span6'})
            odds_raw  = event.find_all('span', {'class' : 'selectboxit-text'})
            times_raw = event.find('span', {'class' :
                                            'event-time-text'}).text.strip()
            teams = [x.text[:-8].strip('1').strip('0') for x in match_raw][:2]
            teams = np.asarray(teams).reshape(2, 1)
            max_bet = [float(x.text[-8:-4]) for x in match_raw]
            date = str(pd.to_datetime(times_raw).date())
            odds = [x.text for x in odds_raw]
            if len(odds) < 6:
                if not any(x for x in odds if x.startswith('+')):
                    odds.insert(0, '+? None')
                    odds.insert(1, '-? None')
                    max_bet.insert(0, np.nan)
                    max_bet.insert(1, np.nan)

                if not any(x for x in odds if x.startswith('ML')):
                    odds.insert(2, 'ML None')
                    odds.insert(3, 'ML None')
                    max_bet.insert(2, np.nan)
                    max_bet.insert(3, np.nan)

                if not any(x for x in odds if x[0].isdigit()):
                    odds.insert(4, 'None None')
                    odds.insert(5, 'None None')
                    max_bet.insert(4, np.nan)
                    max_bet.insert(5, np.nan)

            max_bet = np.asarray(max_bet).reshape(2, -1, order='F')
            date_data = np.asarray([date, date]).reshape(2, 1)
            odds = np.asarray(odds).reshape(2, -1, order='F')
            data = np.concatenate((date_data, teams, odds, max_bet), axis=1)

            cols = ['date', 'team', 'spread', 'ml',
                    'ou', 'smbet', 'mlmbet', 'oumbet']
            tmp = pd.DataFrame(data, columns=cols)
            df =  pd.concat([df, tmp])

        idx = [(i, i) for i in range(int(df.shape[0]/2))]
        df.index = [x for y in idx for x in y]

        df.mlmbet = df.mlmbet.astype(float)

        df['sp'] = df.spread.apply(lambda x: x.split(' ')[0])
        df['sp_odds'] = df.spread.apply(lambda x: x.split(' ')[1])
        df['ml_odds'] = df.ml.apply(lambda x: x.split(' ')[1])

        df.ou = df.ou.astype(str)

        df['over'] = df.ou.apply(lambda x: x.split(' ')[0])
        df['over'].iloc[1::2] = np.nan
        df.over.ffill(inplace=True)

        df['under'] = df.ou.apply(lambda x: x.split(' ')[0])
        df['under'].iloc[::2] = np.nan
        df.under.bfill(inplace=True)

        df['over_odds'] = df.ou.apply(lambda x: x.split(' ')[1])
        df['over_odds'].iloc[1::2] = np.nan
        df.over_odds.ffill(inplace=True)

        df['under_odds'] = df.ou.apply(lambda x: x.split(' ')[1])
        df['under_odds'].iloc[::2] = np.nan
        df.under_odds.bfill(inplace=True)

        df.drop('ou', axis=1, inplace=True)
        df.replace(to_replace='None', value=np.nan, inplace=True)

        self._df = df

    def get_dataframe(self):
        return self._df

    def go_to_sport(self, sport):
        sports = {
          'mlb' : 'sport/baseball/mlb',
          'korean baseball'  : 'sport/baseball/korea-professional-baseball',
          'mexican baseball' : 'sport/baseball/mexican-league',
          'japanese baseball' : 'sport/baseball/nippon-professional-baseball',
          'nfl' : 'sport/football/nfl',
          'ncaa' : 'sport/football/ncaa',
          'uefa' : 'sport/soccer/uefa-champions-league',
          'euro darts' : 'sport/darts/european-darts-tour',
          'euro basket' : 'sport/basketball/fiba-eurobasket-men',
          'ufc' : 'sport/mixed-martial-arts/ufc',
          'nba' : 'sport/basketball/nba'}

        self.go_to_page(page=sports[sport])

class Cloudbet(Browser):
    def __init__(self):
        self._base = "https://www.cloudbet.com/en/sports/"
        self._df   = None
        self._refresh_needed = False

        Browser.__init__(self, base=self._base, open_base=False)

    def parse(self):
        events = self._soup.find_all('div', {'class' : 'all-competitions'})

        lcol = [x.find('div', {'class' : 'left-col'}) for x in events]
        team_html = [x.find_all('span', {'class' : 'team-name-item'})
                    for x in lcol]
        teams = [x.text for y in team_html for x in y]

        rcol = [x.find_all('div', {'class' : 'right-col'}) for x in events]
        col4 = [x.find_all('div', {'class' : 'col4 total'})
               for y in rcol for x in y]

        # Over/Under data
        ou_sp_raw = [x.find_all('div', {'class' : 'short-name'})
                     for y in col4 for x in y]
        ou_sp_raw = [['OTB', 'OTB'] if x==[] else x for x in ou_sp_raw]

        ou_sp_data = [x for y in ou_sp_raw for x in y]
        ou_sp = [x.text.split(' ')[1] if x!='OTB' else x  for x in ou_sp_data]

        over = [(x,x) for x in ou_sp[::2]]
        over = [x for y in over for x in y]

        under = [(x,x) for x in ou_sp[1::2]]
        under = [x for y in under for x in y]

        ou_odds_elem = [x.find_all('span', {'class' : 'odds-element'})
                        for y in col4 for x in y]
        ou_odds_elem = [['OTB', 'OTB'] if x==[] else x for x in ou_odds_elem]
        ou_odds_data = [x for y in ou_odds_elem for x in y]
        ou_odds = [x.text if x!= 'OTB' else x for x in ou_odds_data]

        over_odds = [(x,x) for x in ou_odds[::2]]
        over_odds = [x for y in over_odds for x in y]

        under_odds = [(x,x) for x in  ou_odds[1::2]]
        under_odds = [x for y in under_odds for x in y]

        # Money Line data
        col5 = [x.find_all('div', {'class' : 'col5 2_way'})
                for y in rcol for x in y]
        mltext = [x.text for y in col5 for x in y]
        ml_odds_tup = [(x[:int(len(x)/2)], x[int(len(x)/2):])
                       if 'OTB' not in x
                       else (x.split('OTB')[0], x.split('OTB')[1])
                       for x in mltext]

        ml_odds = [x for y in ml_odds_tup for x in y]

        # # Money Line max bet data
        # ml_odds_elem = [x.find_all('div', {'class' : 'selection 2_way'})
        #                 for y in col5 for x in y]
        # mmlbet = []
        # for elem in ml_odds_elem:
        #     if elem==[]:
        #         mmlbet.append('OTB')
        #         mmlbet.append('OTB')
        #     else:
        #         for odd in elem:
        #             ml_odds.append(odd.text)
        #             mmlbet.append(odd['title'].split(' ')[2])

        # Date
        col1 = self._soup.find_all('div', {'class' : 'col1'})
        time_data = [x.text for x in col1]
        dates = []
        last_date = ''
        for item in time_data:
            if item != 'Now' and item !='live':
                if item[-2:] not in ['AM', 'PM']:
                    last_date = str(pd.to_datetime(item).date())
                else:
                    dates.append(last_date)
                    dates.append(last_date)
            elif item != 'Now':
                dates.append(item)
                dates.append(item)

        data = list(zip(dates, teams, over, over_odds,
                        under, under_odds, ml_odds))

        cols = ['date', 'team', 'over', 'over_odds',
                'under', 'under_odds', 'ml_odds']

        df = pd.DataFrame(data, columns=cols)
        idx = [(i, i) for i in range(int(df.shape[0]/2))]
        df.index = [x for y in idx for x in y]

        df.replace(to_replace='', value='OTB', inplace=True)

        # make sure this doesnt mess anything up
        df.replace(to_replace='OTB', value=np.nan, inplace=True)

        self._df = df

    def get_dataframe(self):
        return self._df

    def go_to_sport(self, sport):
        sports = {'mlb' : 'usa/mlb/c2369',
                  'korean baseball': 'south-korea/kbo-league/c2581',
                  'mexican baseball': 'mexico/mexican-league/c17',
                  'japanese baseball' : 'japan/professional-baseball/c16',
                  'nfl' : 'usa/nfl/c208',
                  'ncaa' : 'usa/ncaa-fcs/c207',
                  'uefa' : 'international-clubs/uefa-champions-league/c716',
                  'euro basket' : 'international/european-championship/c7081',
                  'ufc' : 'international/ufc/c2684',
                  'nba' : 'usa/nba/c143'}
        self.go_to_page(page=sports[sport])

class Betcoin(Browser):
    def __init__(self):
        self._base = "https://sports.betcoin.ag/sport/"
        self._df = None
        self._refresh_needed = True # Check on this

        Browser.__init__(self, base=self._base, open_base=1)

    def parse(self):
        events = self._soup.find_all('div', {'class' : 'event ng-scope'})
        titles = [x.find('a')['title'] for x in events]
        teams = [x for y in
                [(x.split(' vs ')[0], x.split(' vs ')[1]) for x in titles]
                   for x in y]

        year = ' {}'.format(datetime.datetime.today().year)
        times = [x.find('b').text for x in events]
        dates = pd.to_datetime(
                 [x.split(',')[0] + year
                 for y in [(x,x) for x in times] for x in y]
                 ).astype(str)

        # Change to deal when book is closed for certain bets
        ml = [x.text for y in
                 [x.find_all('span', {'class': 'ng-binding'}) for x in events]
                  for x in y if x.text!='']

        # Create data frame
        df_data = list(zip(dates, teams, ml))
        cols = ['date', 'team', 'ml_odds']
        df = pd.DataFrame(df_data, columns=cols)
        idx = [(i, i) for i in range(int(df.shape[0]/2))]
        df.index = [x for y in idx for x in y]

        self._df = df

    def get_dataframe(self):
        return self._df

    def go_to_sport(self, sport):
        sports = {'ncaa' : 'football/7167/33814',
                  'nfl' : 'football/7167/32337',
                  'mlb' : 'baseball/7260/32535',
                  'korean baseball' : 'sport/baseball/7261',
                  'japanese baseball' : 'sport/baseball/7264',
                  'mexican baseball'  : 'sport/baseball/7269'}
        self.go_to_page(page=sports[sport])

class Sportsbet(Browser):
    def __init__(self):
        self._base = "https://sportsbet.io/"
        self._df = None
        self._refresh_needed = True #Check on this

        Browser.__init__(self, base=self._base, open_base=1)

    def parse(self):
        events = self._soup.find_all('div', {'class': 'event-container'})
        t     = [x.find('div', {'class' : 'start'}) for x in events]
        times = [x.find('div').text.split(' ')[0].replace('.','-') for x in t]
        times = [[x, x] for x in times]
        teams_text = [x.find('div', {'class' : 'competitors'}).text
                      for x in events]
        teams =  [x.split(' V ') for x in teams_text]

        odds_elem = [x.find_all('div', {'class' : 'selection-container'})
                     for x in events]

        odds_elem = [x for y in odds_elem for x in y]

        ml_raw = [x.find_all('div', {'class' : 'odds'}) for x in odds_elem]
        ml_raw = [x for y in ml_raw for x in y]
        ml_raw = [x.text for x in ml_raw]

        it = iter(ml_raw)
        ml = [[x[0], x[2]] for x in list(zip(it, it, it))]
        data = list(zip(times, teams, ml))
        data = [list(deepflatten(x, types=list)) for x in data]

        home = [x[::2] for x in data]
        away = [x[1::2] for x in data]

        df_data = [x for y in list(zip(home, away)) for x in y]
        cols = ['date', 'team', 'ml_odds']

        df = pd.DataFrame(df_data, columns=cols)
        idx = [(i, i) for i in range(int(df.shape[0]/2))]
        df.index = [x for y in idx for x in y]

        df.date = pd.to_datetime(df.date, dayfirst=True).astype(str)
        df.replace(to_replace='N/A', value=np.nan, inplace=True)

        self._df = df

    def get_dataframe(self):
        return self._df

    def go_to_sport(self, sport):
        sports = {'korean baseball' : 'sports/pre-live/baseball/south-korea/kbo-league/events/DhuBrJEhGHAuQBeA2',
        'mlb' : 'sports/pre-live/baseball/usa/mlb/events/Xtmznv6tKdmG2LX2F',
        'nfl' : 'sports/pre-live/american-football/usa/nfl-/events/LixxtR6Qs3fFc9iGB',
        'ncaa' : 'sports/pre-live/american-football/usa/ncaaf/events/aqQK8qTCK4WF3ttFw'}
        self.go_to_page(page=sports[sport])
