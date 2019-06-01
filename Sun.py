# save this as Sun.py

import math
import datetime

from time_utils import ConvertUtcToLocalTime


location_coords = {'longitude' : -1.82, 'latitude' : 52.9 }

def get_sun():
    return Sun(location_coords)


class Sun:
    def __init__(self, coords=None):
        if coords is None:
            coords = {'longitude' : -1.82, 'latitude' : 52.9 }
        self.coords = coords

    def getSunriseTimeLocal( self, date=None ):
        sr_utc = self.calcSunTime(True, date)
        return  ConvertUtcToLocalTime(sr_utc['dt'])

    def getSunsetTimeLocal( self, date=None):
        ss_utc =self.calcSunTime(False, date) 
        return ConvertUtcToLocalTime(ss_utc['dt'])

    def calcSunTime( self, isRiseTime, calcdate, zenith = 90.8 ):

        # isRiseTime == False, returns sunsetTime
        if not calcdate:
            calcdate = datetime.datetime.now()
        day = calcdate.day
        month = calcdate.month
        year = calcdate.year

        longitude = self.coords['longitude']
        latitude = self.coords['latitude']

        TO_RAD = math.pi/180

        #1. first calculate the day of the year
        N1 = math.floor(275 * month / 9)
        N2 = math.floor((month + 9) / 12)
        N3 = (1 + math.floor((year - 4 * math.floor(year / 4) + 2) / 3))
        N = N1 - (N2 * N3) + day - 30

        #2. convert the longitude to hour value and calculate an approximate time
        lngHour = longitude / 15

        if isRiseTime:
            t = N + ((6 - lngHour) / 24)
        else: #sunset
            t = N + ((18 - lngHour) / 24)

        #3. calculate the Sun's mean anomaly
        M = (0.9856 * t) - 3.289

        #4. calculate the Sun's true longitude
        L = M + (1.916 * math.sin(TO_RAD*M)) + (0.020 * math.sin(TO_RAD * 2 * M)) + 282.634
        L = self.forceRange( L, 360 ) #NOTE: L adjusted into the range [0,360)

        #5a. calculate the Sun's right ascension

        RA = (1/TO_RAD) * math.atan(0.91764 * math.tan(TO_RAD*L))
        RA = self.forceRange( RA, 360 ) #NOTE: RA adjusted into the range [0,360)

        #5b. right ascension value needs to be in the same quadrant as L
        Lquadrant  = (math.floor( L/90)) * 90
        RAquadrant = (math.floor(RA/90)) * 90
        RA = RA + (Lquadrant - RAquadrant)

        #5c. right ascension value needs to be converted into hours
        RA = RA / 15

        #6. calculate the Sun's declination
        sinDec = 0.39782 * math.sin(TO_RAD*L)
        cosDec = math.cos(math.asin(sinDec))

        #7a. calculate the Sun's local hour angle
        cosH = (math.cos(TO_RAD*zenith) - (sinDec * math.sin(TO_RAD*latitude))) / (cosDec * math.cos(TO_RAD*latitude))

        if cosH > 1:
            return {'status': False, 'msg': 'the sun never rises on this location (on the specified date)'}

        if cosH < -1:
            return {'status': False, 'msg': 'the sun never sets on this location (on the specified date)'}

        #7b. finish calculating H and convert into hours

        if isRiseTime:
            H = 360 - (1/TO_RAD) * math.acos(cosH)
        else: #setting
            H = (1/TO_RAD) * math.acos(cosH)

        H = H / 15

        #8. calculate local mean time of rising/setting
        T = H + RA - (0.06571 * t) - 6.622

        #9. adjust back to UTC
        UT = T - lngHour
        UT = self.forceRange( UT, 24) # UTC time in decimal format (e.g. 23.23)

        #10. Return
        hr = self.forceRange(int(UT), 24)
        minute = int(round((UT - int(UT))*60,0))
        if minute == 60:
            minute = 0
            hr += 1

        try:
            if minute > 59 or minute < 0:
                pass
            sr_date = calcdate.replace(hour=hr,minute=minute,second=0,microsecond=0)
        except:
            pass

        return {
            'status': True,
            'decimal': UT,
            'hr': hr,
            'min': min,
            'dt': sr_date
        }

    def forceRange( self, v, max ):
        # force v to be >= 0 and < max
        if v < 0:
            return v + max
        elif v >= max:
            return v - max

        return v