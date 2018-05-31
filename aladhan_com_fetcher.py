"""Fetches prayer times from 'www.aladhan.com'."""

import json
import requests
import util
from datetime import datetime
import time
from gmaps_client import GetTimezone

_ALADHAN_API_URL = 'http://api.aladhan.com/v1/timings/'
'''
The 'salah.com' API provides a response in the following format:
"Prayers": {
  "2017": { "5": { 17": {
    # actual prayer times yere
    "Fajr": "5 AM"
    ...
  }}}
}
The depth of the useful information (prayer times) is at level 4
'''
_PRAYER_TIMES_RESPONSE_DEPTH = 1


def GetCalcMethod(lat, lng):
  """Returns the Calculation method based on given region

  MWL: Europe and Far East
  ISNA: North America
  Egypt: Africa, Syria, Lebanon
  Umm Al Qura: Arabian Peninsula
  U. of Islamic Sciences: Pakistan, Afganistan, India, Bangladesh

  Args:
    lat: a double representing the latitude
    lng: a double representing the longitude

  Returns: calculation method"""
  
  if lng >= -180 and lng < -30:
    #ISNA
    return 2
  elif lng >= -30 and lng < 35 and lat >= -35 and lat <= 35:
    #EGYPT
    return 5
  elif lng >= 35 and lng < 60 and lat >= 10 and lat <= 30:
    #MAKKAH
    return 4
  elif lng >= 60 and lng < 95 and lat >= 5 and lat <= 40:
    #KAR
    return 1
  else:
    #MWL
    return 3


def GetDailyPrayerTimes(lat, lng, date_str):
  """Gets the daily prayer times from 'salah.com'.

  Performs a POST request on the salah.com prayer times API
  to get today's prayer times (local to timezone of provided
  location).

  Args:
    lat: a double representing the latitude
    lng: a double representing the longitude

  Returns: a dict containing of daily prayer times
  """
  # set up the parameters in the format expected by 'salah.com'
  post_data = { 
      'latitude': lat,
      'longitude': lng,
      'method' : GetCalcMethod(lat, lng),
  }

  user_requested_time = util.GetCurrentUserTime(lat, lng)
  date_time_format = "%Y-%m-%d %H:%M:%S"
  
  if date_str:
    user_time_str = user_requested_time.strftime("%H:%M:%S")
    user_requested_time_str = date_str+' '+user_time_str
    user_requested_time = datetime.strptime(user_requested_time_str, date_time_format)
  
  user_requested_time_UTC = str(int(time.mktime(user_requested_time.timetuple())))

  #print 'post_data = ', post_data
  for request_try in range(3):
    try:
      request = requests.get(_ALADHAN_API_URL+user_requested_time_UTC, params=post_data, timeout=15)
      if request.status_code == requests.codes.ok:
        break
      elif request_try == 2:
        return {}
    except:
      if request_try == 2:
        return {}
      continue

  #print 'here = ', request.text
  response = json.loads(request.text).get("data").get("timings")
  return response
