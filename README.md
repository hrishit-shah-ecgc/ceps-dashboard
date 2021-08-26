# CEPS Dashboard

This project is a website which can help accomplish certain functions that are normally done manually from information in CEPS. It mainly works by having a .CSV file uploaded to it which is gathered from CEPS under weekly reports -> open applications.

It has: 

 - CEPS Status Update (Visual Interface)
 - Print List Generator (File attachment)
 - To Be Assigned Applications (Visual Interface)

# Basic Instructions 

 1. The webapp initially on the main screen where the user has to upload a **.CSV file (not .xlsx)** which contains the open applications currently in CEPS
 2. After hitting the **Let's Go** button the user is taken to the main page where they can select one of the 3 functions from the nav bar above

## Open Apps

 - In the open apps section, the user can select which permit officer
   they wish to see the open applications for
 - After selecting a permit officer, the user can check through various tabs [Processing, MA Reviewing, etc] to see which applications are in what stage
 - The red and orange colours represent the days to the permit standard 
	 - Red = 5 days or less left 
	 - Orange = 10 days or less left

## Print List

In the print list section, the user enter's their CEPS Email and password so that the program can find the applicant names and permit weight factor for applications. 

**None of the Email or Password data is stored by the program. It is simply passed to a Selenium instance to login, and that instance is closed after the processing is done**

The output file is then automatically downloaded as an attachment. 

## To Be Assigned

The to be assigned tab simply lists out the applications which are assigned to: **["Cecile Benoit", "Nasra Farah", "Permit Officer", "Hunting Trophy", Blank]** meaning that they need to be assigned to a permit officer.


# Installation

This program uses **Python and Flask** as the backend with **jinja2 templates** containing HTML and CSS in the frontend. There are various dependencies that need to be installed in order to use this program. They are listed in the **requirements.txt** file

## Running Locally
This program can be run locally using the command: `python app.py`
This will open a localhost:5000 in the browser window


