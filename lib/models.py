import datetime
import json
from urllib.request import urlopen
import time
import colorsys
import bs4
import requests

class LunarData(object):
    def __init__(self):
        self.time = datetime.datetime.now()
        self.__url = r"http://api.burningsoul.in/moon/{0}"
        response = requests.get(self.__url.format(time.mktime(self.time.timetuple())))
        data = json.loads(response.content.decode())
        self.next_fullmoon = datetime.datetime.fromtimestamp(data["FM"]["UT"])
        self.next_newmoon = datetime.datetime.fromtimestamp(data["NNM"]["UT"])
        self.age = data["age"]
        self.illumination = data["illumination"] / 100
        self.stage = data["stage"]
        self.from_earth = data["DFCOE"]
        self.from_sun = data["DFS"]
        self.time_to_full_moon = self.next_fullmoon - self.time
        self.time_to_new_moon = self.next_newmoon - self.time
        self.previous_newmoon = self.time - datetime.timedelta(days=self.age)

    @property
    def previous_full_moon(self):
        url = self.__url.format(time.mktime((self.time - datetime.timedelta(days=28)).timetuple()))
        response = requests.get(url)
        data = json.loads(response.content.decode())
        return datetime.datetime.fromtimestamp(data["FM"]["UT"])

    @property
    def norm_dfcoe(self):
        perigee = 356500
        apogee = 406700
        diff = apogee - perigee
        if self.from_earth <= perigee:
            return 0
        elif self.from_earth >= apogee:
            return 1
        else:
            return (self.from_earth - perigee) / diff

    @property
    def pc_complete(self):
        if self.stage == "waxing":
            return self.age / (self.time_to_full_moon.days + self.age)
        elif self.stage == "waning":
            return self.age / (self.time_to_new_moon.days + self.age)

    def update(self):
        self.__init__()


class TidalData(object):
    def __init__(self):
        self.__url = "https://www.cornwall-beaches.co.uk/north-coast/chapel-porth-weather.htm"
        self.__highs = []
        self.__lows = []
        self.num = 0

    @property
    def next_high(self):
        self.__update()
        return self.__highs[0]

    @property
    def next_low(self):
        self.__update()
        return self.__lows[0]

    @property
    def time_to_low(self):
        self.__update()
        return self.next_low - datetime.datetime.now()

    @property
    def time_to_high(self):
        self.__update()
        return self.next_high - datetime.datetime.now()

    @property
    def next_tide_type(self):
        if self.next_high > self.next_low:
            return "high"
        elif self.next_low > self.next_high:
            return "low"
        else:
            return "?"

    @property
    def time_to_next(self):
        self.__update()
        return min(self.time_to_high, self.time_to_low)

    @property
    def est_pc_complete(self):
        self.__update()
        all = sorted(self.__highs + self.__lows)
        time_between = all[1] - all[0]
        time_elapsed = time_between.seconds - self.time_to_next.seconds
        if time_elapsed < 0:
            time_elapsed = 0
        return float(time_elapsed) / float(time_between.seconds)

    @property
    def led_colour(self):
        c = 0
        if self.next_tide_type == "low":
            c = (self.est_pc_complete / 2) + 0.1
        if self.next_tide_type == "high":
            c = (self.est_pc_complete / 2) + 0.6
            if c > 1:
                c = c - 1
        return c

    def __update(self):
        if any([i for i in (self.__highs + self.__lows) if i < datetime.datetime.now()]) or len(
                self.__lows) == 0 or len(self.__highs) == 0:
            page = urlopen(self.__url)
            soup = bs4.BeautifulSoup(page, "html.parser")
            tides_today = soup.find(id="tideTable").td
            self.__lows, self.__highs = self.__get_times(tides_today, datetime.date.today())
            tides_tomorrow = tides_today.next_sibling
            lows_t, highs_t = self.__get_times(tides_tomorrow, datetime.date.today() + datetime.timedelta(days=1))
            self.__lows += lows_t
            self.__highs += highs_t

    def __get_times(self, soup, date):
        txt_low = [i.b.get_text().replace("Low ", "") for i in soup.find_all("li") if
                   i.b.get_text().startswith("Low ")]
        txt_high = [i.b.get_text().replace("High ", "") for i in soup.find_all("li") if
                    i.b.get_text().startswith("High ")]

        date_low = [datetime.datetime.strptime(" ".join([str(date), i]), "%Y-%m-%d %I:%M%p") for i
                    in txt_low]
        date_high = [datetime.datetime.strptime(" ".join([str(date), i]), "%Y-%m-%d %I:%M%p") for i
                     in txt_high]

        lows = [i for i in date_low if i > datetime.datetime.now()]
        highs = [i for i in date_high if i > datetime.datetime.now()]

        return lows, highs

class NormalLED(object):
    def __init__(self, tides, moon):
        self.r, self.g, self.b = (i * 255 for i in colorsys.hsv_to_rgb(tides.led_colour, moon.norm_dfcoe, moon.illumination))
        self.tuple = (self.r, self.g, self.b)

class PartialLED(object):
    def __init__(self, tides, moon, partial):
        self.r, self.g, self.b = (i * 255 for i in
                      colorsys.hsv_to_rgb(tides.led_colour, moon.norm_dfcoe, moon.illumination * partial))
        self.tuple = (self.r, self.g, self.b)