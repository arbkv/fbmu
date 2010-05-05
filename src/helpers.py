'''
@note: misc helper functions for fb.mu project
@author: arbkv
@license: Apache License, Version 2.0
'''
 
import random 
from google.appengine.api import urlfetch
from django.utils import simplejson

import os.path
from google.appengine.ext.webapp import template



def base62encode(number, alphabet='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'):

    if not isinstance(number, (int, long)):
        raise TypeError('number must be an integer')
    if number < 0:
        raise ValueError('number must be positive')
  
    base62 = ''
    while number != 0:
        number, i = divmod(number, 62)
        base62 = alphabet[i] + base62
 
    return base62

def base62random6():
    return base62encode(random.randint(916132832,56800235583)) #62^5, 62^6-1

''' for future use: '''
def fetch_friends(current_user):
    fetch_url = "http://graph.facebook.com/me/friends?access_token=" + current_user.access_token
    fetch_result = urlfetch.fetch(fetch_url)

    if fetch_result.status_code == 200:
        user_list = simplejson.loads(fetch_result.content)['data']
        uid_list = list()
        for u in user_list:
            uid_list.append(u['id'])
            
    return uid_list

def verify_friendship(current_user,other_user_id):
    other_user_id = unicode(other_user_id)
    currend_user_id = unicode(current_user.id)
    
    if other_user_id == currend_user_id:
        return True
    
    fetch_url = "http://graph.facebook.com/me/friends?access_token=" + current_user.access_token
    fetch_result = urlfetch.fetch(fetch_url)

    if fetch_result.status_code == 200:
        user_list = simplejson.loads(fetch_result.content)['data']
        
        for u in user_list:
            if unicode(u['id']) == other_user_id:
                return True
        
    return False

def debug_out(caller, args):
    args.update({'all__': args})
    path = os.path.join(os.path.dirname(__file__), "d.html")
    caller.response.out.write(template.render(path, args))
    return

    
