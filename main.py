import os, re, configparser, smtplib, requests
from email.mime.text import MIMEText


# FUNCTIONS
def createConfigINI():
    parser['SENDTO'] = {'list': ''}
    parser['MAIN'] = {'url': 'http://eventos.uvanet.br/eventos.php'}
    parser['EMAIL'] = {'username': '', 'password': ''}
    parser['EVENTS'] = {'upcomingeventslistold': '', 'openeventslistold': '', 'closedeventslistold': ''}

    parser.write(open(configPath, 'w', encoding='utf-8'))


def extractSubStr(fullStr, startStr, endStr):
    aux1 = fullStr.partition(startStr)
    aux2 = aux1[1] + aux1[2]
    aux1 = aux2.partition(endStr)
    aux2 = aux1[0] + aux1[1]
    return aux2


def returnListofEvents(fullStr, startStr, endStr):
    listOfEvents, start, end = [], [], []

    for s in re.finditer(startStr, fullStr):
        start.append(s.end())

    for s in re.finditer(endStr, fullStr):
        end.append(s.start())

    for i in range(len(start)):
        listOfEvents.append(fullStr[start[i]:end[i]].replace(',', ';'))

    return listOfEvents


def configArrayReader(sectionStr, optionStr):
    array2 = []
    reading = parser.get(sectionStr, optionStr)
    array1 = reading.split(',')
    for t in array1:
        array2.append(t.strip(' '))
    return array2


def configArrayWriter(sectionStr, optionStr, arrayToWrite):
    s = ""

    for i in range(len(arrayToWrite)):
        s += arrayToWrite[i] + ","

    parser[sectionStr][optionStr] = s


def diff(list1, list2):
    return (list(set(list1) - set(list2)))


def generateEmail(upcoming, openev, closed, mode):
    email = ""

    if mode == 'html':
        email += '<div dir="ltr"><b>&nbsp; &nbsp; &nbsp;</b><u><b><font face = "arial, sans-serif">CADASTRADOS RECENTEMENTE:</font></b></u><div><ul><ul>'
        for i in range(len(upcoming)):
            email += '<li>' + upcoming[i] + '</li>'
        email += '</ul></ul></div><div>'

        email += '<div dir="ltr"><b>&nbsp; &nbsp; &nbsp;</b><u><b><font face = "arial, sans-serif">EVENTOS COM INSCRIÇÕES ABERTAS:</font></b></u><div><ul><ul>'
        for i in range(len(openev)):
            email += '<li>' + openev[i] + '</li>'
        email += '</ul></ul></div><div>'

        email += '<div dir="ltr"><b>&nbsp; &nbsp; &nbsp;</b><u><b><font face = "arial, sans-serif">NOVOS EVENTOS COM INSCRIÇÕES ABERTAS:</font></b></u><div><ul><ul>'
        for i in range(len(closed)):
            email += '<li>' + closed[i] + '</li>'
        email += '</ul></ul></div><div>'

    else:
        email += 'EVENTOS CADASTRADOS RECENTEMENTE:\n'
        for i in range(len(upcoming)):
            email += '\t *'+upcoming[i]+'\n'
        email += '\n'
        email += 'EVENTOS COM INSCRIÇÕES ABERTAS:\n'
        for i in range(len(openev)):
            email += '\t *'+openev[i]+'\n'
        email += '\n'
        email += 'EVENTOS EM OUTRAS ETAPAS:\n'
        for i in range(len(closed)):
            email += '\t *'+closed[i]+'\n'

    return email


def sendEmail(upcoming, openev, closed, mode):
    username = parser.get('EMAIL', 'username')
    password = parser.get('EMAIL', 'password')
    to_addrs = configArrayReader('SENDTO', 'list')

    from_addr = username
    smtp_ssl_host = 'smtp.gmail.com'
    smtp_ssl_port = 465

    message = MIMEText(generateEmail(upcoming, openev, closed, mode), mode)
    message['subject'] = 'Atualização Eventos'
    message['from'] = from_addr
    message['to'] = ', '.join(to_addrs)

    server = smtplib.SMTP_SSL(smtp_ssl_host, smtp_ssl_port)
    server.login(username, password)
    server.sendmail(from_addr, to_addrs, message.as_string())
    server.quit()


# DECLARATING VARIABLES
configPath = 'config.ini'
upcomingEventsListWebsite, openEventsListWebsite, closedEventsListWebsite = [], [], []
upcomingEventsListOld, openEventsListOld, closedEventsListOld = [], [], []

# READING CONFIG.INI
parser = configparser.ConfigParser()
# Check if Config.INI exists, if not, make a new one
if not os.path.exists(configPath):
    createConfigINI()
parser.read(configPath, encoding='utf-8')
url = parser.get('MAIN', 'url')
upcomingEventsListOld = configArrayReader('EVENTS', 'upcomingeventslistold')
openEventsListOld = configArrayReader('EVENTS', 'openeventslistold')
closedEventsListOld = configArrayReader('EVENTS', 'closedeventslistold')

# READING WEBPAGECODE
try:
    websiteSourceCode = requests.get(url)
except:
    print('ERROR: Unable to get webpage sourcecode')

# PROCESSING TEXT TO EXTRACT SUBSTRINGS
strUpcomingEvents = extractSubStr(websiteSourceCode.text, "Novos", "clearDivs")
strOpenEvents = extractSubStr(websiteSourceCode.text, "Inscrições Abertas", "clearDivs")
strClosedEvents = extractSubStr(websiteSourceCode.text, "Outras Etapas", "clearDivs")

# PROCESSING SUBSTRINGS TO GET LIST OF EVENTS
upcomingEventsListWebsite = returnListofEvents(strUpcomingEvents, '"lk_evento">', '</a>')
openEventsListWebsite = returnListofEvents(strOpenEvents, '"lk_evento">', '</a>')
closedEventsListWebsite = returnListofEvents(strClosedEvents, '"lk_evento">', '</a>')

# COMPARING WEBPAGE EVENTS TO CONFIG.INI
diffUpcoming = diff(upcomingEventsListWebsite, upcomingEventsListOld)
diffOpen = diff(openEventsListWebsite, openEventsListOld)
diffClosed = diff(closedEventsListWebsite, closedEventsListOld)

# IF THERE'RE NEW ENTRIES AND Config.INI EVENTS ARE NOT [], SEND EMAIL
if ((diffUpcoming != [] or diffOpen != [] or diffClosed != []) and (
        not (upcomingEventsListOld == [''] and openEventsListOld == [''] and closedEventsListOld == ['']))):
    sendEmail(diffUpcoming, diffOpen, diffClosed, 'html')

# UPDATE Config.INI
configArrayWriter('EVENTS', 'upcomingeventslistold', upcomingEventsListWebsite)
configArrayWriter('EVENTS', 'openeventslistold', openEventsListWebsite)
configArrayWriter('EVENTS', 'closedeventslistold', closedEventsListWebsite)
f = open(configPath, 'w', encoding='utf-8')
parser.write(f)
f.close()
