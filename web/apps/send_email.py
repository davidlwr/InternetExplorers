import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from email.mime.base import MIMEBase
from email import encoders


# print("sending email...")
# template = (''
#             '<img src="data:image/png;base64,{image}">'
#             '{caption}'                              # Optional caption to include below the graph
#             '<br>'
#             '<hr>'
#             '')
class EmailCreator(object):
    template = (''
                '<img src="{graph_url}.png">'  # Use the ".png" magic url so that the latest, most-up-to-date image is included
                '{caption}'  # Optional caption to include below the graph
                '<br>'  # Line break
                '<br>'
                '<hr>'  # horizontal line
                '')

    @staticmethod
    def send_email(images, text_input):
        print("sending email...")
        # email_body = ''
        # _ = template
        # _ = _.format(graph_url=images, caption='')
        # email_body += _

        # email_body = ''
        # for image in images:
        #     _ = template
        #     _ = _.format(image=image, caption='')
        #     email_body += _

        # print(email_body)
        email_user = 'ie.st.bern@gmail.com'
        email_send = 'ie.st.bern@gmail.com'
        subject = 'Python SMTP'

        msg = MIMEMultipart()
        msg['From'] = email_user
        msg['Subject'] = subject
        if text_input:
            body = text_input
        else:
            body = ""
        msg.attach(MIMEText(body, 'html'))

        # filename = "stbern.jpg"
        # attachment = open(filename, 'rb')
        # part = MIMEBase('application', 'octet-stream')
        # part.set_payload(attachment.read())
        # encoders.encode_base64(part)
        # part.add_header('Content-Disposition', "attachment; filename= " + filename)
        # images = images[0]
        count = 0
        for image in images:
            count = count + 1
            part = MIMEBase('image', 'jpeg')
            part.set_payload(image)
            part.add_header('Content-Transfer-Encoding', 'base64')
            content_disposition = 'attachment; filename="graph{}.jpg"'.format(count)
            part['Content-Disposition'] = content_disposition
            msg.attach(part)

        text = msg.as_string()

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(email_user, 'iestbern123')

        server.sendmail(email_user, email_send, text)
        server.quit()
