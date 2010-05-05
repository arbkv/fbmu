'''
@note: implements fb.mu/ service
@author: arbkv
@license: Apache License, Version 2.0
'''


import const
import fbuser
import helpers

import cgi
import os.path

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template
from google.appengine.ext import db


class Message(db.Model):
    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)
    clicks1 = db.IntegerProperty(default=0) #all
    clicks2 = db.IntegerProperty(default=0) #denied
    clicks3 = db.IntegerProperty(default=0) #successfully redirected
    
class Post(db.Model):
    user = db.ReferenceProperty(fbuser.User)
    message = db.ReferenceProperty(Message)
    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)
    clicks1 = db.IntegerProperty(default=0) #all
    clicks2 = db.IntegerProperty(default=0) #denied
    clicks3 = db.IntegerProperty(default=0) #successfully redirected
    

class HomeHandler(fbuser.LoginHandler):

    def get(self):
        args = dict(current_user=self.current_user,
                    facebook_app_id=const.FACEBOOK_APP_ID)

        if self.current_user:
            path = os.path.join(os.path.dirname(__file__), "t_home_loggedin.html")
        else:
            path = os.path.join(os.path.dirname(__file__), "t_home_stranger.html")
            
        self.response.out.write(template.render(path, args))

    def post(self):
        message_store = self.request.get('message')[0:479] #limit length to datastore-compatible
        
        #redirect home in erroneous cases 
        if not self.current_user or message_store == '' or message_store.startswith(('http://fb.mu/', 'http://a.fb.mu/', 'fb.mu/', 'a.fb.mu/')):
            self.redirect('/', permanent=False)
            return
                
        if not message_store.startswith( ('http://', 'https://', 'ftp://', 'xmpp:', 'mailto:') ):
            message_store = 'http://' + message_store
        
        message_display = cgi.escape(message_store)

        #see if URL exists
        message = Message.get_by_key_name(message_store)
        if message == None:
            message = Message(key_name=message_store)

        post_key = helpers.base62random6();
        #check for uniqueness, 10 attempts
        attempts = 10
        while Post.get_by_key_name(post_key):
            post_key = helpers.base62random6();
            attempts -= 1
            if attempts <= 0:
                self.redirect('/', permanent=False)
                return

        message.put()
        
        post = Post(key_name=post_key)
        post.user = self.current_user
        post.message = message
        post.put()
        
        args = {'current_user': self.current_user,
                'facebook_app_id': const.FACEBOOK_APP_ID,
                'key': post_key,
                'message': message_display }

        path = os.path.join(os.path.dirname(__file__), "t_post_result.html")
        self.response.out.write(template.render(path, args))
        
class RedirectHandler(fbuser.LoginHandler):

    def get(self):
        post_key = self.request.path.lstrip('/')
        post = Post.get_by_key_name(post_key)
        if post == None:
            self.redirect('/', permanent=False)
            return
        
        ''' count any click '''
        post.clicks1 += 1
        post.message.clicks1 += 1
         
        if self.current_user:
            if helpers.verify_friendship(self.current_user, post.user.id):
                ''' friends -> redirect: '''
                message = post.message.key().name()
                strRedirect = message
                
                #update stats:
                post.clicks3 += 1
                post.message.clicks3 += 1
                post.message.put()
                post.put()

                self.redirect(strRedirect, permanent=True)
                return
                #todo add some bit.ly-like html later?
            else:
                '''not friends -> denied: '''
                
                #update stats:
                post.clicks2 += 1
                post.message.clicks2 += 1
                post.message.put()
                post.put()

                path = os.path.join(os.path.dirname(__file__), "t_redirect_denied.html")
                args = dict(current_user=self.current_user,
                        post_user=post.user,)
                self.response.out.write(template.render(path, args))
                return
        else:
            
            #update stats:
            post.message.put()
            post.put()
            path = os.path.join(os.path.dirname(__file__), "t_redirect_stranger.html")
            args = dict(
                    facebook_app_id=const.FACEBOOK_APP_ID,
                    post_user=post.user,
                    )
            self.response.out.write(template.render(path, args))
        return

class AboutHandler(fbuser.LoginHandler):

    def get(self):
        args = dict(current_user=self.current_user)
        path = os.path.join(os.path.dirname(__file__), "t_about.html")
        self.response.out.write(template.render(path, args))
        return
        

def main():
    util.run_wsgi_app(webapp.WSGIApplication([
        ("/", HomeHandler),
        ("/about", AboutHandler),
        (r"/.+",RedirectHandler)
            ], debug=True))


if __name__ == "__main__":
    main()
    