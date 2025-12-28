import smtplib, ssl
from email.message import EmailMessage
from os.path import basename
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
import json

with open('config.json', 'r') as config_file:
    config_data = json.load(config_file)

port = config_data["port"]  # For SSL
password = config_data["password"]

# Create a secure SSL context
context = ssl.create_default_context()
sender_email = config_data["username"]
server_hostname = config_data["mailserver"]

def send_mail(send_to, subject, text, files=None):
    msg = MIMEMultipart()
    msg['From'] = config_data["username"]
    msg['To'] = send_to
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject

    msg.attach(MIMEText(text))

    for f in files or []:
        with open(f, "rb") as fil:
            part = MIMEApplication(
                fil.read(),
                Name=basename(f)
            )
        # After the file is closed
        part['Content-Disposition'] = 'attachment; filename="%s"' % basename(f)
        msg.attach(part)


    with smtplib.SMTP_SSL(server_hostname, port, context=context) as server:
        server.login(config_data["username"], password)
        server.send_message(msg)


#send_mail(sender_email, receiver_email, "Testmail", "Dies ist eine Testmail mit Attachement", files=["tex/face.png"] )
