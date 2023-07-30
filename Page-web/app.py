
# Import required libraries
from flask import Flask, redirect, url_for, render_template, request
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
import datetime as dt
import base64
from io import BytesIO
import datetime
from googleapiclient.http import MediaInMemoryUpload
import pickle
import os
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow, InstalledAppFlow
from googleapiclient.discovery import build


# Function to create a Google API service
def Create_Service(client_secret_file, api_name, api_version, *scopes):
    # Print function arguments for debugging purposes
    print(client_secret_file, api_name, api_version, scopes, sep='-')

    # Extracting the required values from the arguments
    CLIENT_SECRET_FILE = client_secret_file
    API_SERVICE_NAME = api_name
    API_VERSION = api_version
    SCOPES = [scope for scope in scopes[0]]

    # Initialize credential variable
    cred = None

    # Define the pickle file name based on the API service and version
    pickle_file = f'token_{API_SERVICE_NAME}_{API_VERSION}.pickle'

    # Check if token exists and load it if available
    if os.path.exists(pickle_file):
        with open(pickle_file, 'rb') as token:
            cred = pickle.load(token)

    # If no valid credentials found, create new ones
    if not cred or not cred.valid:
        if cred and cred.expired and cred.refresh_token:
            # Refresh the credentials if expired and refresh token is available
            cred.refresh(Request())
        else:
            # Run local server flow to authorize and get new credentials
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            cred = flow.run_local_server()

        # Save the new credentials to the pickle file for future use
        with open(pickle_file, 'wb') as token:
            pickle.dump(cred, token)

    try:
        # Build and return the Google API service
        service = build(API_SERVICE_NAME, API_VERSION, credentials=cred)
        print(API_SERVICE_NAME, 'service created successfully')
        return service
    except Exception as e:
        print(e)
    return None


# Global variable
images_file_id = '1J6Cbzo3L4ZELWl-I4cQxOH93nqGSmvA5'

BIKE_NUMBER = 10

# Define the required scope for Google Sheets and Google Drive APIs
scope = ['https://www.googleapis.com/auth/spreadsheets', "https://www.googleapis.com/auth/drive.file",
         "https://www.googleapis.com/auth/drive"]

# Create credentials using the service account JSON key file
creds = ServiceAccountCredentials.from_json_keyfile_name('secret_sheet.json', scope)

# Authorize the client with the credentials
client = gspread.authorize(creds)

# Open the Google Sheets named 'SDP_Test' and 'SDP_Code'
sheet = client.open('SDP_Test').sheet1
code_sheet = client.open('SDP_Code').sheet1

# Save the current credentials to a file
Client_secret = "client_secrets.json"
API_NAME = 'drive'
API_VERSION = 'v3'
SCOPES = ["https://www.googleapis.com/auth/drive"]

# Create a Google Drive API service
service = Create_Service(Client_secret, API_NAME, API_VERSION, SCOPES)


# Could serve me later
def convert_to_RFC_datetime(year=1900, month=1, day=1, hour=0, minute=0):
    """
    Converts the given date and time to RFC 3339 formatted string.
    :param year: Year.
    :param month: Month.
    :param day: Day.
    :param hour: Hour.
    :param minute: Minute.
    :return: RFC 3339 formatted string representing the date and time.
    """
    dt = datetime.datetime(year, month, day, hour, minute, 0).isoformat() + 'Z'
    return dt


# Insert the reservation in the google sheet
def add_reservation_to_spreadsheet(reservation):
    """
    Adds the reservation data to the Google Sheet.
    :param reservation: List containing [last name, first name, date, bike number, reservation status, datetime].
    :return: None
    """
    request_data = sheet.get_all_values()
    last_line_number = len(request_data) + 1
    sheet.insert_row(reservation, last_line_number)
    sheet.sort((3, 'des'))


# Remove the reservation from the google sheet
def remove_reservation_from_spreadsheet(reservation):
    """
    Removes the reservation data from the Google Sheet.
    :param reservation: List containing [last name, first name, date, bike number, reservation status, datetime].
    :return: Bool
    """
    request_data = sheet.get_all_values()
    df = pd.DataFrame(request_data)
    df.columns = ['Last Name', 'First Name', 'Date', 'Datetime', 'Bike Number']
    flag = False

    for i in df.index:
        if [df['Last Name'][i], df['First Name'][i], df['Date'][i], df['Bike Number'][i]] == reservation[0:4]:
            line_number = i + 1
            sheet.delete_rows(line_number)
            flag = True

    sheet.sort((3, 'des'))
    return flag


# Check if bikes are available given a date
def check_bike_availability(date):
    """
    Checks if bikes are available on the given date.
    :param date: Date to check for bike availability.
    :return: Tuple (availability, bike number), where availability is a bool (True if bikes are available, False otherwise)
             and bike number is the first available bike number if available, or -1 if no bikes are available.
    """
    request_data = sheet.get_all_values()
    df = pd.DataFrame(request_data)
    if len(df) == 0:
        return True, 1
    df.columns = ['Last Name', 'First Name', 'Date', 'Datetime', 'Bike Number']
    N = 0
    bike_avail = [i for i in range(1, 11)]
    for i in df.index:
        if df['Date'][i] == date:
            N += 1
            bike_avail.remove(int(df['Bike Number'][i]))
        if N == BIKE_NUMBER:
            return False, -1
    return True, bike_avail[0]


# This function was used to store the pictures on the google drive but another way was found
# Still in the code if needed later
def render_picture(data):
    """
    Renders the image data to a base64 encoded string.
    :param data: Image data to be rendered.
    :return: Base64 encoded string representing the image.
    """
    render_pic = base64.b64encode(data).decode('ascii')
    return render_pic


# Crucial Function that add the images of the bike taken by the users directly on the google drive
def add_photo_to_drive(img, img_name):
    """
    Uploads the photo to Google Drive.
    :param img: Image data to be uploaded.
    :param img_name: Name of the image file.
    :return: None
    """
    file_name = img_name

    file_meta = {
        'name': file_name,
        'parents': [images_file_id]
    }

    media = MediaInMemoryUpload(img)
    service.files().create(
        body=file_meta,
        media_body=media,
        fields='id'
    ).execute()


# Return the bike code given the n° of the bike
def get_bike_code(bike_Num):
    """
    Gets the code for a given bike number from the code spreadsheet.
    :param bike_Num: Bike number for which the code is required.
    :return: Bike code corresponding to the given bike number.
    """
    request_data = code_sheet.get_all_values()
    df = pd.DataFrame(request_data)
    df.columns = ['Bike Code']

    return df['Bike Code'][bike_Num]


# Initialize the Flask app
app = Flask(__name__)


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/login")
def login():
    return render_template("reservation.html")


@app.route("/login", methods=["POST", "GET"])
def reservation():
    if request.method == "POST":
        user_name = request.form["last_name"]
        user_pname = request.form["first_name"]
        user_date = request.form["date"]

        today = dt.datetime.now()
        date = dt.datetime.strptime(user_date, '%Y-%m-%d')

        avail, bike_Num = check_bike_availability(user_date)

        if avail and (date > today):
            reservation = [str(user_name).lower(), str(user_pname).lower(), str(user_date), str(dt.datetime.now()),
                           str(bike_Num)]
            add_reservation_to_spreadsheet(reservation)
            code = get_bike_code(bike_Num)
            return validation(user_name, user_pname, user_date, bike_Num, code)

        else:
            return invalidation(user_date)
    else:
        return render_template("home.html")


@app.route("/logout")
def logout():
    return render_template("logout.html")


@app.route("/logout", methods=["POST", "GET"])
def return_bike():
    if request.method == "POST":
        user_name = request.form["last_name"]
        user_pname = request.form["first_name"]
        user_date = request.form["date"]
        bike_Num = request.form["bike_number"]
        image = request.files["image"]
        data = image.read()
        im = bytearray(data)
        img_name = str(user_name) + '_' + str(user_date) + '.png'
        reservation = [str(user_name).lower(), str(user_pname).lower(), str(user_date), str(bike_Num)]
        removed = remove_reservation_from_spreadsheet(reservation)
        if removed:
            add_photo_to_drive(im, img_name)
            return validation_return()

        else:
            return invalidation_return()

    else:
        return render_template("home.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/<validation>")
def validation(last_name, first_name, date, bike_number, bike_code):
    return f"""<p2>Reservation request registered for <I><B>{last_name} {first_name} </B> on <B>{date}</B></I> <br> Bike number is <B>{bike_number}<B><br> Bike code is <B>{bike_code}<B></p2>""" \
           f""" <nav><ul><li><a href="/"> Home </a></li></ul></nav>"""


@app.route("/<invalidation>")
def invalidation(date):
    return f"<p2>No available slots for {date}, please try another date.</p2>" \
           f""" <nav><ul><li><a href="/login"> Make a Reservation </a></li></ul></nav>"""


@app.route("/<validation_return>")
def validation_return():
    return f"<p2>The bike has been returned successfully. We look forward to seeing you again! \n You may now leave the page or go back to the homepage.</p2>" \
           f"""<nav><ul><li><a href="/"> Back to Homepage </a></li></ul></nav>"""


@app.route("/<invalidation_return>")
def invalidation_return():
    return f"<p2>The request was not processed. Are the provided information valid?</p2>" \
           f""" <nav><ul><li><a href="/logout"> Return a Bike </a></li></ul></nav>"""


if __name__ == "__main__":
    app.run(debug=True)
