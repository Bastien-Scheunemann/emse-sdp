
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

Nombre_velo = 10

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


def convert_to_RFC_datetime(year=1900, month=1, day=1, hour=0, minute=0):
    dt = datetime.datetime(year, month, day, hour, minute, 0).isoformat() + 'Z'
    return dt


# Insert the reservation in the google sheet
def insertion(reservation):
    """
    :param reservation: liste [nom, pnom, date, numvelo, etat_reservation, datetime]
    :return: void
    put the reservation into the spreadsheet SDP
    """
    request_data = sheet.get_all_values()
    LastLineNumber = len(request_data) + 1
    sheet.insert_row(reservation, LastLineNumber)
    sheet.sort((3, 'des'))


# Remove the reservation from the google sheet
def ejection(reservation):
    """
    :param reservation: liste [nom, pnom, date, numvelo, etat_reservation, datetime]
    :return: Bool
    put the reservation into the spreadsheet SDP
    """
    request_data = sheet.get_all_values()
    df = pd.DataFrame(request_data)
    df.columns = ['Nom', 'Prénom', 'date', 'datetime', 'bike_Num']
    flag = False

    for i in df.index:
        if [df['Nom'][i], df['Prénom'][i], df['date'][i], df['bike_Num'][i]] == reservation[0:4]:
            LineNumber = i + 1
            sheet.delete_rows(LineNumber)
            flag = True

    sheet.sort((3, 'des'))
    return flag


# Check if bikes are available given a date
def available(date):
    request_data = sheet.get_all_values()
    df = pd.DataFrame(request_data)
    if len(df) == 0:
        return True, 1
    df.columns = ['Nom', 'Prénom', 'date', 'datetime', 'bike_Num']
    N = 0
    bike_avail = [i for i in range(1, 11)]
    for i in df.index:
        if df['date'][i] == date:
            N += 1
            bike_avail.remove(int(df['bike_Num'][i]))
        if N == Nombre_velo:
            return False, -1
    return True, bike_avail[0]


def render_picture(data):
    render_pic = base64.b64encode(data).decode('ascii')
    return render_pic


def ajout_photo(img, img_name):
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


def get_code(bike_Num):

    request_data = code_sheet.get_all_values()
    df = pd.DataFrame(request_data)
    df.columns = ['Bike_Code']

    return df['Bike_Code'][bike_Num]


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
        user_name = request.form["nm"]
        user_pname = request.form["pm"]
        user_date = request.form["dt"]

        today = dt.datetime.now()
        date = dt.datetime.strptime(user_date, '%Y-%m-%d')

        avail, bike_Num = available(user_date)

        if avail and (date > today):
            reservation = [str(user_name).lower(), str(user_pname).lower(), str(user_date), str(dt.datetime.now()),
                           str(bike_Num)]
            insertion(reservation)
            code = get_code(bike_Num)
            return validation(user_name, user_pname, user_date, bike_Num, code)

        else:
            return invalidation(user_date)
    else:
        return render_template("home.html")


@app.route("/logout")
def logout():
    return render_template("logout.html")


@app.route("/logout", methods=["POST", "GET"])
def rendre_velo():
    if request.method == "POST":
        user_name = request.form["nm"]
        user_pname = request.form["pm"]
        user_date = request.form["dt"]
        bike_Num = request.form["bn"]
        image = request.files["image"]
        data = image.read()
        im = bytearray(data)
        img_name = str(user_name) + '_' + str(user_date) + '.png'
        reservation = [str(user_name).lower(), str(user_pname).lower(), str(user_date), str(bike_Num)]
        supp = ejection(reservation)
        if supp:
            ajout_photo(im, img_name)
            return validation_suppression()

        else:
            return invalidation_suppression()

    else:
        return render_template("home.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/<validation>")
def validation(nm, pm, dt, bn, bc):
    return f"""<p2>Demande de prêt enregistrée au nom de <I><B>{nm} {pm} </B> le <B>{dt}</B></I> <br> Le numéros du vélo est <B>{bn}<B><br> Le code du vélo est <B>{bc}<B></p2>""" \
           f""" <nav><ul><li><a href="/"> Home </a></li></ul></nav>"""


@app.route("/<invalidation>")
def invalidation(date):
    return f"<p2>Pas de place pour cette date {date}, essayez une autre date svp</p2>" \
           f""" <nav><ul><li><a href="/login"> Faire une réservation </a></li></ul></nav>"""


@app.route("/<validation_suppression>")
def validation_suppression():
    return f"<p2>Le vélo a bien été rendu, au plaisir de vous revoir parmi nous ! \n Vous pouvez quitter la page ou revenir à l'accueil</p2>" \
           f"""<nav><ul><li><a href="/"> Retour à l'accueil </a></li></ul></nav>"""


@app.route("/<invalidation_suppression>")
def invalidation_suppression():
    return f"<p2>La demande n'a pas abouti, les informations sont-elles valides ?</p2>" \
           f""" <nav><ul><li><a href="/logout"> Rendre un vélo </a></li></ul></nav>"""


if __name__ == "__main__":
    app.run(debug=True)
