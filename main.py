import os, urllib

from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp.util import login_required
from google.appengine.ext import db

#Generate an error page, this can be called directly or invoked by an exception
def errorpage(caller, errortext="There was an error that occured", exc=None):
    template_values = {'errortext': errortext}
    if not exc is None:
        template_values["errormessage"] = exc.message
    gen_params(caller.request, template_values)
    path = os.path.join(os.path.dirname(__file__), 'errorpage.html')
    caller.response.out.write(template.render(path, template_values))
    
#Generate all of the params used by our base template
def gen_params(request, params=None):
    user = users.get_current_user()
    
    if params is None:
        params = {}    
        
    if user:
        params['user'] = user
        params['sign_out'] = users.CreateLogoutURL('/')
        params['is_admin'] = users.IsCurrentUserAdmin() 
    else:
        params['sign_in'] = users.CreateLoginURL(request.path)
    
    #Get the pages for our left hand navigation
    pages_query = db.Query(Page)
    pages_query.filter('display =', True)
    pages_query.order('title')
    pages = pages_query.fetch(25)
    params['left_nav'] = pages
    
    #Retreive information about our environment to properly generate links
    params['appid'] = os.environ.get("APPLICATION_ID")
    if "Development" in os.environ.get("SERVER_SOFTWARE"):
        params['is_production'] = False
    else:
        params['is_production'] = True
    
    return params

#Data model for our Page entities 
class Page(db.Model):
    author = db.UserProperty()
    date = db.DateTimeProperty(auto_now_add=True)
    title = db.StringProperty()
    display = db.BooleanProperty()
    secure = db.BooleanProperty()

#Data model for our PageContent entities
class PageContent(db.Model):
    author= db.UserProperty()
    content = db.TextProperty()
    date = db.DateTimeProperty(auto_now_add=True)
    page = db.ReferenceProperty(Page, collection_name="versions")
    
class MainPage(webapp.RequestHandler):
    def get(self):
        self.redirect("/wiki/Main_Page")
             
class CreatePage(webapp.RequestHandler):
    @login_required
    def get(self):
        try: 
            #Retrieve a page name from the url query string
            page_name = self.request.get("pagename")
            page_name = urllib.unquote(page_name)
            page_name = page_name.replace("_", " ")
            
            #Generate the template values and merge the template with the values 
            template_values = {'pagename': page_name}
            gen_params(self.request, template_values)
            path = os.path.join(os.path.dirname(__file__), 'createpage.html')
            self.response.out.write(template.render(path, template_values))
        except Exception, exc:
            errorpage(self,exc=exc)
            
    def post(self):
        try:
            #Check if the user is logged in
            if not users.get_current_user():
                #Redirect to the error page, the user does not have permission
                errorpage(self,"You do not have permission to perform this action!")
                return
            
            page  = Page(key_name = self.request.get('title'))            
            page.author = users.get_current_user()
            page.title = self.request.get('title')
            page.secure = False
            page.display = True
            page_id = page.put()
            
            pagecontent = PageContent()
            pagecontent.page = page_id
            pagecontent.content = page.title
            pagecontent.author = users.get_current_user()    
            pagecontent.put()
            
            self.redirect('/editpage?pageid=' + str(page_id))
        except Exception, exc:
            errorpage(self,exc=exc)
        
class EditPage(webapp.RequestHandler):
    def get(self):
        try:
            #Check if a version ID is supplied, and if so retrieve the content view the version
            if self.request.get("versionid"):
                pagecontent = db.get(self.request.get("versionid"))
                page_id = pagecontent.page.key
                page = pagecontent.page
            #No version was supplied so retrieve the content view the pageid
            else:
                page_id = db.Key(self.request.get('pageid'))
                page = db.get(page_id)

                #Get the latest version to edit
                pagecontent = page.versions.order("-date")[0]
            
            #Check if the page is secure and if the user is not logged in
            if page.secure == True and not users.GetCurrentUser():
                #Redirect the user to the login page
                self.redirect(users.create_login_url(self.request.url))
                return
            
            #Generate the template values and merge the template with the values   
            template_values = {'pagecontent': pagecontent}
            gen_params(self.request, template_values)
            path = os.path.join(os.path.dirname(__file__), 'editpage.html')
            self.response.out.write(template.render(path, template_values))
            
        except Exception, exc:
            errorpage(self,exc=exc)
            
    def post(self):
        try:
            page_id = db.Key(self.request.get('pageid'))
            pagecontent = PageContent()        
            page = db.get(page_id)

            #Check if the page is secure and the user is not logged in
            if page.secure == True and not users.GetCurrentUser():
                #Redirect to the error page, the action is not allowed
                errorpage(self,"You do not have permission to perform that action!")
                return
        
            #Check if the user is logged in
            if users.get_current_user():
                #Assign the author if the user is logged in
                pagecontent.author = users.get_current_user()     
        
            #Create a new page version
            pagecontent.page = page_id
            pagecontent.content = self.request.get('content') 
            pagecontent.put()
        
            #Redirect back to viewing the page
            self.redirect('/viewpage?pageid=' + str(page_id))
        except Exception, exc:
            errorpage(self,exc=exc)
    
class ViewPage(webapp.RequestHandler):
    def get(self):
        try:
            #Retrieve by pageid
            if self.request.get('pageid'):
                page_id = db.Key(self.request.get('pageid'))
                page = db.get(page_id)
                pagecontent = page.versions.order("-date")[0]
            
            #Retrieve by versionid
            if self.request.get('versionid'):
                version_key = db.Key(self.request.get('versionid'))
                pagecontent = db.get(version_key)
            
            #Generate the template values and merge the template with the values 
            template_values = {'pagecontent': pagecontent}
            gen_params(self.request, template_values)
            path = os.path.join(os.path.dirname(__file__), 'viewpage.html')
            self.response.out.write(template.render(path, template_values))
        except Exception, exc:
            errorpage(self,"There was an error retrieving the page",exc)
        
class ViewWikiPage(webapp.RequestHandler):

    def get(self):
        try:
            #Retrieve the wiki page to get view the dynamic URL
            page_name = self.request.path.replace("/wiki/","")
            page_name = urllib.unquote(page_name)
            page_name = page_name.replace("_", " ")
            page = Page.get_by_key_name(page_name)
        
            #This code is executed the first time when the app is installed
            #The user is redirected to create the Main Page from any empty datastore
            if (not page) and page_name == "Main Page":
                self.redirect("/createpage?pagename=Main_Page")
                return
            
            #Get the latest version of the page
            pagecontent = page.versions.order("-date")[0]
            
            #Generate the template values and merge the template with the values 
            template_values = {'pagecontent': pagecontent}
            gen_params(self.request, template_values)
            path = os.path.join(os.path.dirname(__file__), 'viewpage.html')
            self.response.out.write(template.render(path, template_values))       
        
        except Exception, exc:
            errorpage(self, "There was an error retrieving the page",exc)

class MangePages(webapp.RequestHandler):
    @login_required
    def get(self):
        try:
            pages_query = Page.all().order('title')
            pages = pages_query.fetch(25)
        
            #Generate the template values and merge the template with the values 
            template_values = {'pages': pages}
            gen_params(self.request, template_values)
            path = os.path.join(os.path.dirname(__file__), 'managepages.html')
            self.response.out.write(template.render(path, template_values))
        except Exception, exc:
            errorpage(self,exc=exc)
                   
class PageAction(webapp.RequestHandler):
    
    @login_required
    def get(self):
        try:
            #Check if the user is an admin
            if not users.IsCurrentUserAdmin():
                #Tell the user they don't have permission if they're not an admin
                errorpage(self,"You do not have permission to perform this action!")
                return
            
            #Retrieve the page
            page_id = db.Key(self.request.get('pageid'))
            page = db.get(page_id)
        
            #If the action is delete then delete the page
            if self.request.get('action') == "delete":
                page.delete()
            
            #If the action is secure then toggle the secure flag
            elif self.request.get('action') == "secure":
                if page.secure == True:
                    page.secure = False
                else:
                    page.secure = True 
                page.put()
            #If the action is display then toggle the display flag
            elif self.request.get('action') == "display":
                if page.display == True:
                    page.display = False
                else:
                    page.display = True
                page.put()
            #redirect back to the manage page after the action
            self.redirect('/managepages')
        except Exception, exc:
            errorpage(self,exc=exc)
            
class PageVersions(webapp.RequestHandler):
    def get(self):
        try:
            #Retrieve the page and versions of the page
            page_id = db.Key(self.request.get('pageid'))
            page = db.get(page_id)
            versions = page.versions.order("-date")
            num_versions = page.versions.count()
        
            #Generate the template values and merge the template with the values 
            template_values = {'page': page, 'versions':versions, 'num_versions':num_versions}
            gen_params(self.request, template_values)
            path = os.path.join(os.path.dirname(__file__), 'pageversions.html')
            self.response.out.write(template.render(path, template_values))
        except Exception, exc:
            errorpage(self,exc=exc)        

application = webapp.WSGIApplication(
                                      [('/createpage', CreatePage),
                                      ('/editpage',EditPage),
                                      ('/viewpage',ViewPage),
                                      ('/managepages',MangePages),
                                      ('/pageaction',PageAction),
                                      ('/pageversions',PageVersions),
                                      ('/wiki/.*', ViewWikiPage),
                                      ('/*',MainPage)],
                                      debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
