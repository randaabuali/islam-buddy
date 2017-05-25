# Intent handler for 'WHEN_IS_START_TIME_INTENT'

import response_builder
import gmaps_API
from prayer_info import PrayerInfo
import util


class StartTimeIntentHandler(object):

  INTENTS_HANDLED = [
      'WHEN_IS_START_TIME_INTENT',
      'PERMISSION_INTENT',
  ]

  def __init__(self, prayer_info):
    self.prayer_info_ = prayer_info


  def _EncodeParameter(self, param):
    return ' '.join(param).encode('utf-8')


  def _GetContext(self, post_params, context_name):
    for candidate in post_params.get('result').get('contexts'):
      if candidate['name'] == context_name:
        return candidate
    return None


  def HandleIntent(self, device_params, post_params):
    """Returns a server response as a dictionary."""
    
    # we have the user's city
    params = post_params.get('result').get('parameters')
    city = params.get('geo-city')
    country = params.get('geo-country')
    state = params.get('geo-state-us')

    # we have the user's lat/lng
    has_location = 'location' in device_params

    # if there is no city or location, we won't be able to do anything
    # so request the user for permissions to use their location
    if not (city or has_location):
      # do not ask for permission if we've already asked for it before
      permission_context = self._GetContext(post_params, 'actions_intent_permission')
      if (permission_context and 
          permission_context.get('parameters').get('PERMISSION') == 'false'):
        # if we are here it means the user rejected our request to use location
        return {'speech': ('Sorry, I\'ll need a location in order to get a prayer time.'
                           ' You can also try asking prayer times for a city next time.')}

      # the user has specified a state or country but not a city, then we should
      # instruct them to tell us a city name.
      if state or country:
        return {'speech': ('Sorry, I don\'t have enough information. Please try '
                           'again with a city next time.')}

      print ('Could not find location in request, '
             'so responding with a permission request.')
      return response_builder.RequestLocationPermission()

    # we must fill these parameters in order to make a query to salah.com
    lat = None
    lng = None
    desired_prayer = params.get('PrayerName')

    # if we have a city, then use this
    if city:
      print 'city:', city 
      print 'country:', country 
      print 'state:', state 
      city = self._EncodeParameter(params.get('geo-city'))

      if country:
        country = self._EncodeParameter(params.get('geo-country'))

      if state:
        state = self._EncodeParameter(params.get('geo-state-us'))

      location_coordinates = gmaps_API.GetGeocode(city, country, state)
      lat = location_coordinates.get('lat')
      lng = location_coordinates.get('lng')

    # if we have a device location, then use it
    elif has_location:
      relevant_context = self._GetContext(post_params, 'requ')
      print 'rel context = ', relevant_context
      if relevant_context:
        print 'relevant_context = ', relevant_context

        location = device_params.get('location')
        city = location.get('city')
        lat = location.get('coordinates').get('latitude')
        lng = location.get('coordinates').get('longitude')

        # Since this is a follow-on query, we won't actually have the
        # prayer name in the 'result.parameters.PrayerName'. Instead
        # we must pull it from the context.
        desired_prayer = relevant_context.get('parameters').get('PrayerName')
      else:
        print 'Could not find relevant context!'

    all_prayer_times = self.prayer_info_.GetPrayerTimes(lat, lng)
    prayer_time = \
       all_prayer_times.get(util.StringToDailyPrayer(desired_prayer))
    print 'prayer_times[', desired_prayer, "] = ", prayer_time 

    return self._MakeSpeechResponse(desired_prayer, prayer_time, city)


  def _MakeSpeechResponse(self, desired_prayer, prayer_time, city):
    if desired_prayer.lower() == 'suhur':
      return {'speech': 'Suhur ends at %s in %s' % (prayer_time, city)}
    else:
      return {
        'speech': 
            ('The time for %s is %s in %s.' % 
             (desired_prayer, prayer_time, city))
      }

