"""Utility functions."""
import json
from datetime import datetime, timedelta
import pytz
from flask import make_response
from common import DailyPrayer, CalculationMethod
from gmaps_client import GetTimezone

_GEONAMES_URL = 'http://api.geonames.org/timezoneJSON?formatted=true'


def EncodeParameter(param, spaced=False):
    """Returns param encoded to utf-8"""
    if spaced:
        return ' '.join(param).encode('utf-8')
    return ''.join(param).encode('utf-8')


def JsonResponse(response_dict):
    """Constructs a JSON response object."""
    response = make_response(json.dumps(response_dict, indent=4))
    response.headers['Content-Type'] = 'application/json'
    return response


def JsonError(error_text):
    """Constructs a JSON response from an error."""
    response = make_response(json.dumps({'error': error_text}, indent=4))
    response.headers['Content-Type'] = 'application/json'
    return response


_PRAYER_METADATA = {
    DailyPrayer.FAJR: {
        'key_name': 'fajr',
        'display_name': 'Fajr',
        'pronunciation': 'Fajer',
    },
    DailyPrayer.SUNRISE: {
        'key_name': 'sunrise',
        'display_name': 'Sunrise',
        'pronunciation': 'Sunrise',
    },
    DailyPrayer.DHUHR: {
        'key_name': 'dhuhr',
        'display_name': 'Dhuhr',
        'pronunciation': 'Dhuhr',
    },
    DailyPrayer.ASR: {
        'key_name': 'asr',
        'display_name': 'Asr',
        'pronunciation': 'Usser',
    },
    DailyPrayer.MAGHRIB: {
        'key_name': 'maghrib',
        'display_name': 'Maghrib',
        'pronunciation': 'Mugreb',
    },
    DailyPrayer.ISHA: {
        'key_name': 'isha',
        'display_name': 'Isha',
        'pronunciation': 'Isha',
    },
    DailyPrayer.QIYAM: {
        'key_name': 'qiyam',
        'display_name': 'Qiyam',
        'pronunciation': 'Qiyam',
    },
    DailyPrayer.UNSPECIFIED: {
        'key_name': 'unpsecified',
        'display_name': 'unspecified',
        'pronunciation': 'unspecified',
    },
}

_KEY_NAME_TO_PRAYER = {
    'suhur': DailyPrayer.FAJR,
    'fajr': DailyPrayer.FAJR,
    'sunrise': DailyPrayer.SUNRISE,
    'dhuhr': DailyPrayer.DHUHR,
    'asr': DailyPrayer.ASR,
    'maghrib': DailyPrayer.MAGHRIB,
    'iftar': DailyPrayer.MAGHRIB,
    'isha': DailyPrayer.ISHA,
    'qiyam': DailyPrayer.QIYAM,
    'unspecified': DailyPrayer.UNSPECIFIED,
}

_COUNTRY_TO_CALCULATION_METHOD = {
    'pakistan': CalculationMethod.KAR,
    'india': CalculationMethod.KAR,
    'afghanistan': CalculationMethod.KAR,
    'bangladesh': CalculationMethod.KAR,
    'egypt': CalculationMethod.EGYPT,
    'syria': CalculationMethod.EGYPT,
    'lebanon': CalculationMethod.EGYPT,
    'malaysia': CalculationMethod.EGYPT,
    'iran': CalculationMethod.TEHRAN,
    'bahrain': CalculationMethod.GULF,
    'iraq': CalculationMethod.GULF,
    'yemen': CalculationMethod.GULF,
    'oman': CalculationMethod.GULF,
    'united arab emirates': CalculationMethod.GULF,
    'kuwait': CalculationMethod.KUWAIT,
    'qatar': CalculationMethod.QATAR,
    'singapore': CalculationMethod.SINGAPORE,
    'france': CalculationMethod.FRANCE,
    'turkey': CalculationMethod.TURKEY,
    'unspecified': CalculationMethod.UNSPECIFIED,
}

def GetPrayerKeyName(daily_prayer):
    """Gets the name of a daily prayer (ex: "fajr")."""
    return _PRAYER_METADATA.get(daily_prayer).get('key_name')


def _StringToEnum(str_value, str_to_enum, default):
    """Converts a string to an enum based on provided dict."""
    str_value = str(str_value).lower()
    if str_value in str_to_enum:
        return str_to_enum[str_value]
    return default


def StringToDailyPrayer(prayer_str):
    """Infers a DailyPrayer out of a string."""
    prayer_str = str(prayer_str).lower()
    if prayer_str in _KEY_NAME_TO_PRAYER:
        return _KEY_NAME_TO_PRAYER[prayer_str]
    return ''


def CountryToCalculationMethod(country_str):
    """Infers a CalculationMethod out of a string."""
    country_str = str(country_str).lower()
    if country_str in _COUNTRY_TO_CALCULATION_METHOD:
        return _COUNTRY_TO_CALCULATION_METHOD[country_str]
    return 0


def ConvertTimeToAMPM(time_str):
    """Converts Time from 24H to 12H AM/PM"""
    org_time_format = '%H:%M'
    convert_time_format = '%I:%M %p'

    return datetime.strptime(time_str, org_time_format).strftime(convert_time_format)


def GetPronunciation(daily_prayer):
    """Gets TTS for a daily prayer."""
    #print 'GetPronunciation: ', _PRAYER_METADATA[daily_prayer]
    return _PRAYER_METADATA[daily_prayer].get('pronunciation')


def GetDisplayText(daily_prayer):
    """Gets display text for a daily prayer."""
    return _PRAYER_METADATA[daily_prayer].get('display_name')


def GetCurrentUserTime(user_lat, user_lng):
    """Returns the current time in the user's timezone."""
    (gmaps_timezone_str, dst_UTC_offset, raw_UTC_offset) = GetTimezone(user_lat, user_lng)
    if gmaps_timezone_str is None or gmaps_timezone_str == 'None':
      return (None, None, None)
    user_timezone = pytz.timezone(gmaps_timezone_str)
    user_time = datetime.now(user_timezone)
    return (user_time, dst_UTC_offset, raw_UTC_offset)


def GetTimeDifference(user_time_datetime, prayer_time):
    """Returns the time difference in hours and minutes
    between the current user time and the given prayer time."""
    prayer_time_format = '%I:%M %p'
    prayer_time_datetime = datetime.strptime(prayer_time, prayer_time_format)
    start_time = datetime.combine(datetime.min, user_time_datetime.time())
    end_time = datetime.combine(datetime.min, prayer_time_datetime.time())
    if start_time > end_time:
        end_time += timedelta(1)
    time_diff = (end_time - start_time).total_seconds()
    result = {}
    result['HOURS'] = int(time_diff//3600)
    result['MINUTES'] = int((time_diff%3600) // 60)
    result['SECONDS'] = int((time_diff%60))
    return result

