# use python2, email stuff doesn't work in python3
# need to allow less secure apps in the "from" email:
# https://myaccount.google.com/u/5/lesssecureapps?pageId=none

import arrow
import requests
import json
import smtplib
import sys

from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText


def send_mail(user, pw, message, to):
    gmailUser = user + '@gmail.com'
    gmailPassword = pw
    recipient = to

    msg = MIMEMultipart()
    msg['From'] = gmailUser
    msg['To'] = recipient
    msg['Subject'] = "Airfare Alert!"
    msg.attach(MIMEText(message))

    mailServer = smtplib.SMTP('smtp.gmail.com', 587)
    mailServer.ehlo()
    mailServer.starttls()
    mailServer.ehlo()
    mailServer.login(gmailUser, gmailPassword)
    mailServer.sendmail(gmailUser, recipient, msg.as_string())
    mailServer.close()


def print_key(d, key, tabs=0):
    return "    " * tabs + key + ": " + d[key] + "\n"


def print_results(res, airline_codes):
    """Return string of result details or None if no results."""
    if "tripOption" not in res["trips"].keys():
        return None

    text = ""
    for trip in res["trips"]["tripOption"]:
        text += print_key(trip, "saleTotal")
        text += "\n"
        for slice in trip["slice"]:
            for seg in slice["segment"]:
                text += "duration: " + str(seg["duration"] / float(60)) + " hrs\n"
                airline = airline_codes[seg["flight"]["carrier"]]
                text += "flight.carrier: " + airline + "\n"
                for leg in seg["leg"]:
                    text += print_key(leg, "origin", tabs=1)
                    text += print_key(leg, "destination", tabs=1)
                    text += print_key(leg, "departureTime", tabs=1)
                    text += print_key(leg, "arrivalTime", tabs=1)
        text += "\n\n"

    print(text)
    return(text)


def find_fares(origin, dest, depart, comeback, maxprice, key):
    """Return API request response.

    :param origin: string, airport code e.g. BOS
    :param dest: string, airport code, e.g. LAX
    :param depart: string, depart date, e.g. "2017-09-01"
    :param comeback: string, return date, e.g. "2017-09-01"
    :param maxprice: string, dollar amaount, e.g. "USD250.00"
    :param key: string, google api key
    """
    data = {
        "request": {
            "passengers": {
                "adultCount": 1
            },
            "slice": [
                {
                    "origin": origin,
                    "destination": dest,
                    "date": depart
                },
                {
                    "origin": dest,
                    "destination": origin,
                    "date": comeback
                }
            ],
            "maxPrice": maxprice
        }
    }

    json_data = json.dumps(data)

    headers = {"Content-Type": "application/json"}

    params = {"key": key}

    r = requests.post('https://www.googleapis.com/qpxExpress/v1/trips/search',
                      params=params, headers=headers, data=json_data)

    print(r.status_code)

    return r.json()


def read_to_dict(filename):
    with open(filename, "r") as f:
        d = {}
        for line in f:
            key = line.split("=")[0]
            val = line.split("=")[1].strip()
            d[key] = val
    return d


if __name__ == "__main__":

    env = read_to_dict(".env")
    airlines = read_to_dict("airline_codes.txt")

    d = arrow.get(2013, 5, 5)
    c = d.shift(days=+4)
    print d.format('YYYY-MM-DD')
    print c.format('YYYY-MM-DD')

    res = find_fares("BOS", "LAX", "2017-09-01", "2017-10-01", "USD500.00",
                     env['apikey'])

    msg = print_results(res, airlines)

    if len(sys.argv) < 2:
        sys.exit("no recipient email --> no email sent")

    if msg is not None:
        send_mail(env['email'], env['password'], msg, sys.argv[1])
