
# Online Bicycle Reservation Website

This is a Flask-based web application for an online bicycle reservation website. The application allows users to reserve bicycles for specific dates and return them after use. It utilizes the Google Sheets and Google Drive APIs to store and manage reservation data and related images.

# Prerequisites

Before running the application, make sure you have the following requirements installed:

Python (version 3.x)
Flask
gspread
pandas
oauth2client
google-api-python-client
You can install the required dependencies using the following command:

bash
Copy code
pip install Flask gspread pandas oauth2client google-api-python-client
How to Run

Clone or download the repository.
Install the required dependencies as mentioned above.
Create a Google Sheets file named 'SDP_Test' and another file named 'SDP_Code' in your Google Drive.
Generate the secret_sheet.json file and store it in the root directory. This JSON file should contain the credentials for accessing the Google Sheets API.
Replace the client_secrets.json file with your own Google Drive API credentials.
Update the images_file_id variable with the corresponding Google Drive folder ID where you want to store the uploaded images.
Start the application by running the app.py file:
bash
Copy code
python app.py
Features

Home Page: The landing page of the website displaying basic information about the service.
Reservation Page: Allows users to make bicycle reservations by providing their name, date, and other required details. The reservation will be processed only if the date is in the future and there are available bicycles for that date.
Invalidation Page: If the requested date is not available for reservation, the user will be redirected to this page with a notification to try another date.
Validation Page: After successful reservation, the user will be redirected to this page, showing the details of the reservation, including the assigned bicycle number and its unique code.
Logout Page: The page where users can return the rented bicycle. They need to provide their name, date, and bicycle number for verification. They can also upload an image of the returned bicycle. If the details match an existing reservation, the reservation will be removed from the system, and the image will be stored in the specified Google Drive folder.
Invalidation Suppression Page: If the return details do not match any existing reservation, the user will be redirected to this page with a notification to check the provided information.
Validation Suppression Page: After successful return and reservation removal, the user will be redirected to this page, confirming the successful return.
Functionality

The application connects to the Google Sheets API to handle reservation data storage and retrieval.
It verifies the availability of bicycles for a given date before confirming a reservation.
Users can return bicycles by providing their name, date, and bicycle number, and the application will match the information with existing reservations.
Returned bicycles' images are uploaded to a specified Google Drive folder.
Bicycle codes for each reserved bicycle are retrieved from the 'SDP_Code' Google Sheets file.
Important Notes

The application uses Flask as the web framework, which can be customized as per your requirements.
Ensure proper security measures are implemented for handling sensitive data such as API credentials.
Please feel free to contact me if you have any questions or feedback on this project. Happy coding! #BicycleReservation #FlaskApplication #GoogleSheetsAPI #GoogleDriveAPI #PythonWebApp
