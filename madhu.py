import os
from pydantic_ai.settings import ModelSettings

BASE_URL = f"http://localhost:8000/v1"

os.environ["BASE_URL"]    = BASE_URL
os.environ["OPENAI_API_KEY"] = "abc-123"   

print("Config set:", BASE_URL)

from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

provider = OpenAIProvider(
    base_url=os.environ["BASE_URL"],
    api_key=os.environ["OPENAI_API_KEY"],
)

agent_model = OpenAIModel("Qwen3-30B-A3B", settings=ModelSettings(temperature=0.0), provider=provider)

from pydantic_ai import Agent

agent = Agent(
    model=agent_model
)
import asyncio
from pydantic_ai.mcp import MCPServerStdio
async def run_async(prompt: str) -> str:
    async with agent.run_mcp_servers():
        result = await agent.run(prompt)
        return result.output

from typing import List, Dict
from pydantic_ai import Tool
import json
from datetime import datetime, timezone, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import dateutil.parser

@Tool
def retrieve_calendar_events(user: str, start: str, end: str) -> List[Dict]:
    """
    Retrieve calendar events for a specific user between start and end times.
    
    Args:
        user: Email address of the user whose calendar to check
        start: Start time in ISO format (e.g., '2023-12-01T09:00:00')
        end: End time in ISO format (e.g., '2023-12-01T17:00:00')
        
    Returns:
        List of event dictionaries with StartTime, EndTime, NumAttendees, Attendees, and Summary
    """
    events_list = []
    token_path = "Keys/"+user.split("@")[0]+".token"
    user_creds = Credentials.from_authorized_user_file(token_path)
    calendar_service = build("calendar", "v3", credentials=user_creds)
    events_result = calendar_service.events().list(
        calendarId='primary', 
        timeMin=start,
        timeMax=end,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    events = events_result.get('items', [])
    
    for event in events:
        attendee_list = []
        try:
            for attendee in event["attendees"]: 
                attendee_list.append(attendee['email'])
        except KeyError: 
            attendee_list.append("SELF")
        start_time = event["start"].get("dateTime", event["start"].get("date"))
        end_time = event["end"].get("dateTime", event["end"].get("date"))
        events_list.append({
            "StartTime": start_time, 
            "EndTime": end_time, 
            "NumAttendees": len(set(attendee_list)), 
            "Attendees": list(set(attendee_list)),
            "Summary": event.get("summary", "No title")
        })
    return events_list

agent = Agent(
    model=agent_model,
    tools=[retrieve_calendar_events],
    system_prompt="""
    You are an AI scheduling assistant. Follow these steps:

    1. **Input Analysis**:
       - Parse the meeting request:
         - Organizer: {From}
         - Attendees: {Attendees[*].email}
         - Duration: 1 hour (from EmailContent)
         - Preferred day: Monday (from EmailContent)
         - Location: {Location}

    2. **Priority handling**:
       - Check EmailContent for keywords: ["urgent", "priority", "ASAP", "important"]
       - If found, escalate to priority handling
       
    3. **Time Suggestion Logic**:
       - Fetch calendar events for all attendees for:
         - Date range: Preferred day: Monday/Tuesday (from EmailContent) 8AM-6PM IST
         - Timezone: +05:30 (IST)
        - Find which attendee is busy in the preferred slot. The slot will always occur in the future from DateTime (from EmailContent). 
       - Find the earliest Duration: (from EmailContent) slot where:
         1. All attendees are free
         2. Preferably between 10AM-5PM work hours
         3. Avoid lunch hours (1PM-2PM)
         4. Avoid time after 6PM. (decline politely)



    4. **Output Format** (JSON):
       ```json
       {   "Priority": urugent/not urugent (from EmailContent)
           "PreferredTime":
                 "StartTime": "YYYY-MM-DDTHH:MM:SS+05:30",
                 "EndTime": "YYYY-MM-DDTHH:MM:SS+05:30",
                   { "ConflictCheck" on  Preferred day: Monday/Tuesday (from EmailContent): {
                   "userone.amd@gmail.com": "Available",
                   "usertwo.amd@gmail.com": "Available",
                   "userthree.amd@gmail.com": "Available"
               }}
           "ProposedTime": {
               "StartTime": "YYYY-MM-DDTHH:MM:SS+05:30",
               "EndTime": "YYYY-MM-DDTHH:MM:SS+05:30",
               "ConflictCheck": {
                   "userone.amd@gmail.com": "Available",
                   "usertwo.amd@gmail.com": "Available",
                   "userthree.amd@gmail.com": "Available"
               }
           },
           "AlternativeSlots": [
               {
                   "StartTime": "YYYY-MM-DDTHH:MM:SS+05:30",
                   "EndTime": "YYYY-MM-DDTHH:MM:SS+05:30"
               }
           ]

        "MetaData": {
        "Subject": "Agentic AI Project Status Update",
        "Location": "Virtual",
        "Organizer": "organizer@example.com",
        "Attendees": ["userone@example.com", "usertwo@example.com", "userthree@example.com"]
         },
        "PoliteEmailDraft": if priotiy  (from EmailContent){
            "Subject": "Proposed Meeting: Agentic AI Project",
            "Body": request the busy attendee to reschedule their committment if its priority at the preferred time. Otherwise send a mail to the team at the proposed time. If the preferred time is beyond 6pm, decline politely.
       }
       ```
    """
)

async def test_run(data):
    return await run_async(data)
