The project is built using the Google App Engine SDK and built-in Python libraries.  The App Engine SDK can be obtained from http://code.google.com/appengine/downloads.html.

View a sample site running this application at http://wikipythonwiki.appspot.com

To install a development version of the system in Windows:
1.	Download Google App Engine SDK
2.	Install the SDK
3.	Extract the wikipythonwiki source zip file
4.	Launch the Google App Engine Launcher Application
5.	Click File -> Add Existing Application
6.	Browse to the extracted source code
7.	Click Add
8.	Click Run
9.	Click Browse
10.	The system will launch a default browser to the location of the locally installed app
11.	The first time you run the application it will ask you to log in, and then redirect you to the create page where you need to create the Main Page article.  Everything will be automatically filled in, just click login and then create page.  The system will then redirect you to the Main Page editor where you can either edit the page or click home to bring you to the homepage.
Deploying the Application to Google:
1.	Create a new application at http://appengine.google.com 
2.	Edit the app.yaml file in the source code so that the application: identifier in app.yaml matches the name of the application you created on the app engine website.
3.	In Google App Engine Launcher click deploy
4.	Enter your app engine email and password and then click ok
5.	Once complete the application should be fully deployed
6.	Browse to the application at <appname>.appsot.com
7.	The first time you run the application it will ask you to log in, and then redirect you to the create page where you need to create the Main Page article.  Everything will be automatically filled in, just click login and then create page.  The system will then redirect you to the Main Page editor where you can either edit the page or click home to bring you to the homepage.
