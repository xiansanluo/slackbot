#!/usr/bin/python
#coding:utf-8
import os
import requests
import base64
import hmac
import hashlib
import random
import time
import operator
from luis_sdk import LUISClient
from slackclient import SlackClient
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

# starterbot's ID as an environment variable
BOT_ID = os.environ.get("BOT_ID")
# constants
AT_BOT = "<@" + BOT_ID + ">"
# instantiate Slack & Twilio clients
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))
NONCE = int(random.random()*1000)
SECRETID = os.environ.get('SECRETID')
SECRETKEY = os.environ.get('SECRETKEY')
REGION = "gz"
TIMESTAMP = int(time.time())

# translate chinese to english
def get_trans(command):
    sig = {
        'Action': 'TextTranslate',
        'Nonce': NONCE,
        'Region': REGION,
        'SecretId': SECRETID,
        'Timestamp': TIMESTAMP,
        'sourceText': command,
        'source': "zh",
        'target': 'en'
    }
    sigl = sorted(sig.iteritems(), key=operator.itemgetter(0))
    for i, val in enumerate(sigl):
        if i == 0:
            sigstr = val[0] + '=' + str(val[1])
        else:
            sigstr = sigstr + '&' + val[0] + '=' + str(val[1])
    sigstr = "GETtmt.api.qcloud.com/v2/index.php?" + sigstr
    signature = (base64.b64encode(hmac.new(SECRETKEY, sigstr, hashlib.sha1).digest()))
    payload = {
        'Action': 'TextTranslate',
        'Nonce': NONCE,
        'Region': REGION,
        'SecretId': SECRETID,
        'Timestamp': TIMESTAMP,
        'Signature': signature,
        'sourceText': command,
        'source': "zh",
        'target': 'en'
    }
    try:

        r = requests.get('https://tmt.api.qcloud.com/v2/index.php', params=payload)
        if r.status_code == requests.codes.ok:
            return r.json()["targetText"]
        else:
            return command
    except Exception,e:
        print "error:",e
        return command


def handle_command(command, channel):
    qna_ans, qna_sco = qna_result(command)
    luis_ans, luis_sco, entities = luis_result(command)
    if (qna_sco > luis_sco and qna_ans != "None") or (qna_ans != "None" and luis_ans == "None"):
        print "use qna answer"
        slack_client.api_call("chat.postMessage", channel=channel,
                          text=qna_ans, as_user=True)
    elif qna_sco == luis_sco :
        slack_client.api_call("chat.postMessage", channel=channel,
                          text="Sorry, i can not understand", as_user=True)
    else:
        print "use luis answer"
        handle_luis(luis_ans, entities, channel)

def handle_luis(luis_ans, entities, channel):
    print "luis answer:", luis_ans, entities
    if luis_ans == 'kibana':
        if len(entities):
            for entity in entities:
                if entity.get_type() == 'env' and entity.get_name() == 'prod':
                    slack_client.api_call("chat.postMessage", channel=channel,
                                          text='''Make sure you connect prod vpn,and then click: http://k.llsops.com/''',
                                          as_user=True)
                elif entity.get_type() == 'env':
                    slack_client.api_call("chat.postMessage", channel=channel,
                                          text='''Make sure you connect staging vpn,and then click: http://stag.k.llsops.com/''',
                                          as_user=True)
                else:
                    print "entity:", entity
                    slack_client.api_call("chat.postMessage", channel=channel,
                                          text='''Make sure you connect staging vpn,and then click: http://stag.k.llsops.com/''',
                                         as_user=True)
        else:
            print "no entity"
            slack_client.api_call("chat.postMessage", channel=channel,
                                  text='''Make sure you connect staging vpn,and then click: http://stag.k.llsops.com/''',
                                  as_user=True)
    elif luis_ans == 'BookFlight':
        for entity in entities:
            print entity.get_name
            slack_client.api_call("chat.postMessage", channel=channel,
                                  text='''bookflight test''',
                                  as_user=True)
    else:
        slack_client.api_call("chat.postMessage", channel=channel,
                            text="Sorry, i can not understand", as_user=True)

def qna_result(question):
    payload = {"question": question}
    headers = {"Content-Type": "application/json", "Ocp-Apim-Subscription-Key": "03355e84f71840f8b9ab5a1f68a7b07e"}
    url = '/knowledgebases/498c3249-5bca-4309-8d84-84a17217681a/generateAnswer'
    host = 'https://westus.api.cognitive.microsoft.com/qnamaker/v2.0'
    r = requests.post(host + url, json=payload, headers=headers)
    if r.status_code == requests.codes.ok:
        answers = r.json()["answers"]
        score = 0
        text = "None"
        for answer in answers:
            if answer["score"] > score:
                score = answer["score"]
                text = answer["answer"]
        print "question:", question
        print "qna result:", text, score
        return text, float(score)
    else:
        return "None", 0

def luis_result(question):
    try:
        appid = '1e995b1e-35a7-4349-ae58-e90f9beb6cca'
        appkey = '9fa67485043a4605ab8e8220eb80a940'
        text = question
        client = LUISClient(appid, appkey, True)
        res = client.predict(text)
        print "luis result:", res.get_top_intent().get_name(), float(res.get_top_intent().get_score()) * 100, res.get_entities()
        return res.get_top_intent().get_name(), float(res.get_top_intent().get_score()) * 100, res.get_entities()
    except Exception, exc:
        print(exc)
        return "None", 0, None

def process_res(res):
    print(u'Query: ' + res.get_query())
    print(u'Top Scoring Intent: ' + res.get_top_intent().get_name())
    if res.get_dialog() is not None:
        if res.get_dialog().get_prompt() is None:
            print(u'Dialog Prompt: None')
        else:
            print(u'Dialog Prompt: ' + res.get_dialog().get_prompt())
        if res.get_dialog().get_parameter_name() is None:
            print(u'Dialog Parameter: None')
        else:
            print('Dialog Parameter Name: ' + res.get_dialog().get_parameter_name())
        print(u'Dialog Status: ' + res.get_dialog().get_status())
    print(u'Entities:')
    for entity in res.get_entities():
        print(u'"%s":' % entity.get_name())
        print(u'Type: %s, Score: %s' % (entity.get_type(), entity.get_score()))



def parse_slack_output(slack_rtm_output):
    """
        The Slack Real Time Messaging API is an events firehose.
        this parsing function returns None unless a message is
        directed at the Bot, based on its ID.
    """
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'text' in output and AT_BOT in output['text']:
                # return text after the @ mention, whitespace removed
                return output['text'].split(AT_BOT)[1].strip().lower(), \
                       output['channel']
    return None, None


if __name__ == "__main__":
    READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
    if slack_client.rtm_connect(with_team_state=True):
        print("StarterBot connected and running!")
        while True:
            command, channel = parse_slack_output(slack_client.rtm_read())
            if command and channel:
                print '---------------------------'
                print 'Origin Question:', command
                command = get_trans(command)
                handle_command(command, channel)
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("Connection failed. Invalid Slack token or bot ID?")