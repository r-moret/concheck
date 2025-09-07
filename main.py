import os
import sys
import resend
import argparse
import requests

from lxml import html
from pathlib import Path
from datetime import datetime

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
FROM_MAIL = os.getenv("CONCHECK_FROM")

def notify(mail: str):
    resend.api_key = RESEND_API_KEY

    now = datetime.now().strftime("%d/%m/%Y - %H:%M")
    mail_template = Path("template.html").read_text()

    params: resend.Emails.SendParams = {
        "from": f"Concheck Script <{FROM_MAIL}>",
        "to": [mail],
        "subject": f"Concheck: condition satisfied on {now}",
        "html": mail_template.format(receiver=mail, satisfaction_time=now),
    }

    resend.Emails.send(params)   

def main(text: str, condition: str, notification_mail: str | None):
    tree = html.fromstring(text)
    satisfies_condition = tree.xpath(condition)

    if not isinstance(satisfies_condition, bool):
        raise TypeError("The condition used didn't give a boolean result, make sure you are passing a restriction and not a search path")
    
    if not satisfies_condition:
        print('FINISHED: condition not satisfied.')
        return

    print('FINISHED: condition satisfied.')

    if notification_mail:
        notify(notification_mail)
        print('FINISHED: notification sent.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('html', help='HTML text of the webpage to analyze', nargs='?', default=None)
    parser.add_argument('-u', '--url', help='URL of the webpage to analyze', required=False, default=None)
    parser.add_argument('-p', '--xpath', help='XPath with the condition to check for', required=True)
    parser.add_argument('-n', '--notify', help='Email to notify when the condition is detected as satisfied', required=False, default=None)
    args = parser.parse_args()

    if args.url:          # URL specified
        response = requests.get(args.url)
        response.raise_for_status()
        
        text = response.text
    elif args.html:       # HTML positional specified
        text = args.html
    else:                 # HTML piped
        text = sys.stdin.read() if not sys.stdin.isatty() else None

    if not text:
        raise ValueError('You must either pass directly the content of the webpage you want to check or the URL to obtain the content (--url)')
    
    if args.notify:
        if not FROM_MAIL:
            raise ValueError('No sending mail was found, to be notified you must provide one')    
        if not RESEND_API_KEY:
            raise ValueError('No Resend API key was found, please provide one to be notified')

    main(text, args.xpath, args.notify)
