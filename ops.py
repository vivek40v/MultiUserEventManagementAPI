import smtplib
from email.mime.text import MIMEText
from settings import settings
from db_ops import DBHandler
import requests
from common import logger
from passlib.context import CryptContext
from jose import JWTError, jwt
import os
import subprocess
from datetime import datetime, timedelta
import secrets
import urllib.parse
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
import pandas as pd

# Password Hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = secrets.token_hex(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
oauth2_scheme = APIKeyHeader(name="Authorization", auto_error=True)


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.now() + (expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_admin(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_role = payload.get("role")
        if user_role != "admin":
            raise credentials_exception
        return payload
    except JWTError:
        raise credentials_exception

def get_current_organizer(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_role = payload.get("role")
        if user_role != "organizer":
            raise credentials_exception
        return payload
    except JWTError:
        raise credentials_exception

def event_join(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_role = payload.get("role")
        if user_role in ["organizer", "admin", "attendee"]:
            raise credentials_exception
        return payload
    except JWTError:
        raise credentials_exception


def email_send(emaildict):
    receiver_email = emaildict['receiver_email'][0] if isinstance(emaildict['receiver_email'], list) else emaildict[
        'receiver_email']

    # Create email message
    msg = MIMEText(emaildict['body'])
    msg["Subject"] = emaildict['subject']
    msg["From"] = settings.SMTP_USERNAME
    msg["To"] = receiver_email  # Ensure it's a string

    try:

        with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
            server.starttls()  # Secure the connection
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_USERNAME, receiver_email, msg.as_string())

        print("Email sent successfully!")
    except Exception as e:
        logger.error(f"Error: {e}")

def get_public_ip():
    """Fetch the public IP address of the system"""
    response = requests.get("https://api64.ipify.org?format=json")
    return response.json().get("ip")

def get_mac_address(ip):
    """Get the MAC address of an IP in the local network."""
    try:
        if os.name == "nt":  # Windows
            output = subprocess.check_output(f"arp -a {ip}", shell=True).decode()
            for line in output.split("\n"):
                if ip in line:
                    return line.split()[1]
        else:  # Linux/macOS
            output = subprocess.check_output(f"arp -n {ip}", shell=True).decode()
            for line in output.split("\n"):
                if ip in line:
                    return line.split()[2]
    except Exception as e:
        return f"Error: {e}"
    return "MAC address not found"


def get_location_from_ip(ip_address: str):
    """Fetch location details from ipinfo.io"""
    url = f"https://ipinfo.io/{ip_address}/json"
    try:
        response = requests.get(url)
        data = response.json()
        latitude, longitude = data["loc"].split(",")
        return {
            "status": "True",
            "ip": ip_address,
            "city": data.get("city"),
            "region": data.get("region"),
            "country": data.get("country"),
            "latitude": latitude,
            "longitude": longitude
        }
    except Exception as e:
        logger.error(f"{ip_address}: {e}")
        return {"status": False, "ip": ip_address, "error": "Location not found"}

def get_location_using_gmap(place_name, api_key):
    """
    Fetches the latitude and longitude of a place using the Google Maps Geocoding API.

    Args:
        place_name: The name of the place to search for (e.g., "Paris, France").
        api_key: Your Google Maps Geocoding API key.

    Returns:
        A dictionary containing the latitude and longitude, or None if the location
        could not be found or an error occurred.
    """
    base_url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": place_name,
        "key": api_key,
    }

    try:
        url = f"{base_url}?{urllib.parse.urlencode(params)}" #Construct the url with the parameters
        response = requests.get(url)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        data = response.json()

        if data["status"] == "OK":
            location = data["results"][0]["geometry"]["location"]
            return location
        else:
            print(f"Geocoding API returned status: {data['status']}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None
    except (KeyError, IndexError) as e:
        print(f"An error occurred while parsing the response: {e}")
        return None



def register_user_ops(user, request):
    user_ip = request.client.host
    hashed_password = pwd_context.hash(user.password)

    params = {'contactnumber': user.ContactNumber,
              'username': user.username,
              'email': user.email,
              'pwd': hashed_password,
              "dob": user.DOB,
              'role': user.role,
              "ipaddress": user_ip,
              "eventlocation": user.eventlocation,
              "eventdate": user.eventdate,
              "eventname": user.eventname,
              'active': True}

    dbres = DBHandler.AddNewUser(params)
    userid = dbres.fetchone()[0]

    email_subject = f"Welcome to {user.eventname}"
    receiver_email = [user.email]
    email_body= (f"Thanks for registering for the event {user.eventname}, location {user.eventlocation} for event date {user.eventdate}\n"
                 f"your username for login is {user.ContactNumber} and userid {userid}!")
    email_payload = {"subject": email_subject, "receiver_email": receiver_email, "body" : email_body}
    email_send(email_payload)

    return userid
    # public_ip = get_public_ip()
    # location_data = get_location_from_ip(public_ip)
    # print(location_data)
    #
    # mac_address = get_mac_address(user_ip)
    # location_data = get_location_from_ip(mac_address)
    # print(location_data)

    # db_user = User(username=user.username, email=user.email, password=hashed_password)
    # db.add(db_user)
    # db.commit()
    # db.refresh(db_user)
    # return db_user

    # return location_data


def authenticate_user(user):
    userinfo = DBHandler.get_user_data(user.username)
    print(userinfo)
    if not user or not pwd_context.verify(user.password, userinfo[4]):
        return False, ''
    return True, userinfo[6]


def delete_user_by_admin(userid):
    return DBHandler.delete_user(userid)


def get_all_user_details():
    return DBHandler.get_allusers()


def update_user_by_admin(userinfo):

    print(userinfo)
    update_values = userinfo.dict(exclude_none=True)  # Fetch only non-None values
    contactnumber = update_values['ContactNumber']
    del update_values['ContactNumber']
    if not update_values:
        return {"message": "No valid fields provided for update"}

    return DBHandler.update_user_info(update_values, contactnumber)


def create_event(event, organizer):
    userid = DBHandler.verifyuser(organizer.get("username"))
    print(userid)
    if userid != event.userid:
        return False, "Invalid organizerid"
    return True, DBHandler.create_newevent(event)[0]


def getall_events():
    dbres=DBHandler.getallevents()

    rows = dbres.fetchall()  # Fetch all rows
    headers = dbres.keys()  # Get column names

    # Convert to DataFrame
    df = pd.DataFrame(rows, columns=headers)
    df.drop_duplicates(subset=['title', 'description', 'location', 'datetime_from', 'datetime_to', 'max_attendees'], keep = 'first', inplace=True)
    df.sort_values(by = 'datetime_from', inplace=True)
    return df.to_dict(orient='records')


def update_event_details(event):
    event_values = event.dict(exclude_none=True)  # Fetch only non-None values
    userid = DBHandler.verifyuser(event_values.get("username"))
    if userid != event.userid:
        return "Organizer is not valid"
    eventid = event_values.get("eventid")
    del event_values['eventid']

    return DBHandler.update_event_details(event, eventid)



def delete_event(eventid, userid):

    return DBHandler.delete_event(eventid, userid)
























