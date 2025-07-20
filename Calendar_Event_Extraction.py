#!/usr/bin/env python
# coding: utf-8

# # Google Calendar Event Fetcher
# 
# #### The Notebook demonstrates how to programmatically retrieve and process Google Calendar events for a given user and date range.
# 
# ##### Key Steps:
# 
# Authentication: Load user credentials from a token file.
# 
# API Call: Fetch events between specified start/end dates using the Google Calendar API.
# 
# Data Processing: Extract event details (start/end times, attendees) and structure them into a clean format.
# 
# Output: Return a list of events with attendee counts and time slots.
# ```

# ### Importing Required Libraries

# In[1]:


import json
from datetime import datetime, timezone, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


# ### Defining the retrive_calendar_events Function that includes : 
# #### 1. Authenticating with Google Calendar
# #### 2. Fetching Events
# #### 3. Processing Events & Structuring

# In[2]:


def retrive_calendar_events(user, start, end):
    events_list = []
    token_path = "Keys/"+user.split("@")[0]+".token"
    user_creds = Credentials.from_authorized_user_file(token_path)
    calendar_service = build("calendar", "v3", credentials=user_creds)
    events_result = calendar_service.events().list(calendarId='primary', timeMin=start,timeMax=end,singleEvents=True,orderBy='startTime').execute()
    events = events_result.get('items')

    for event in events : 
        attendee_list = []
        try:
            for attendee in event["attendees"]: 
                attendee_list.append(attendee['email'])
        except: 
            attendee_list.append("SELF")
        # start_time = event["start"]["dateTime"]
        # end_time = event["end"]["dateTime"]
        start_time = event["start"].get("dateTime", event["start"].get("date"))
        end_time = event["end"].get("dateTime", event["end"].get("date"))
        events_list.append(
            {"StartTime" : start_time, 
             "EndTime": end_time, 
             "NumAttendees" :len(set(attendee_list)), 
             "Attendees" : list(set(attendee_list)),
             "Summary" : event["summary"]})
    return events_list


# ### Calling ```retrive_calendar_events``` with Auth Token, Start Date & End Date 
# #### Date Format : YYYY-MM-DD (T) HH:MM:SS +TIMEZONE (+5:30 Indicates IST Time Zone Asia/Kolkata ) 

# In[7]:


event = retrive_calendar_events("userone.amd@gmail.com", '2025-07-21T00:00:00+05:30', '2025-07-22T23:59:59+05:30')


# ### Output that describing sample event : 

# In[8]:


event


# In[ ]:




