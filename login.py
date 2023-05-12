"""
vklass cli

Usage:
  vklass <action> <username> <password>
"""
import requests
import json
from operator import itemgetter
from datetime import datetime, date

def login(user, pwd):
  headers = {'User-Agent':'Mozilla/5.0 (X11; Linux x86_64; rv:108.0) Gecko/20100101 Firefox/108.0',
    'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language':'sv-SE,sv;q=0.8,en-US;q=0.5,en;q=0.3',
    'Accept-Encoding':'gzip, deflate, br',
    'Connection':'keep-alive',
    'Upgrade-Insecure-Requests':'1',
    'Sec-Fetch-Dest':'document',
    'Sec-Fetch-Mode':'navigate',
    'Sec-Fetch-Site':'none',
    'Sec-Fetch-User':'1',
    'TE':'trailers'
  }

  s = requests.Session()
  r = s.get('https://auth.vklass.se/saml/initiate?idp=https%3A%2F%2Fauth.goteborg.se%2Fidp%2Fsps%2Fskola%2Fsaml20&org=189', headers = headers)

  headers["Host"] = "auth.goteborg.se"
  headers["Origin"] = "https://auth.goteborg.se"
  headers["Referer"] = "https://auth.goteborg.se/auth/login"

  path = r.text.split('form class="c-form" method="POST" name="loginform" id="loginform" action="')[1].split('"')[0]
  keytarget = r.text.split('input type="hidden" name="templateTarget" value="')[1].split('"')[0]

  r2 = s.post('https://auth.goteborg.se'+path, data={'username':user,'password':pwd,'operation':'verify','gbgtemplate':'login','templateTarget':keytarget}, headers = headers)

  if r2.text.__contains__('name="SAMLResponse" value="'):
    saml = r2.text.split('name="SAMLResponse" value="')[1].split('"')[0]
  else:
    raise Exception("Fel lösenord / användarnamn")

  headers["Origin"] = "https://auth.goteborg.se"
  headers["Referer"] = "https://auth.goteborg.se/"


  kakor = requests.utils.dict_from_cookiejar(s.cookies)
  kakorlogin = {
	"saml-session":kakor["saml-session"],
	"_tpc_persistance_cookie":kakor["_tpc_persistance_cookie"],
        "BBN01b9bc29":kakor["BBN01b9bc29"],
  }

  s2 = requests.Session()
  requests.utils.add_dict_to_cookiejar(s2.cookies,kakorlogin)
  headers["Host"] = "auth.vklass.se"
  r3 = s2.post('https://auth.vklass.se/saml/assertion', data={"RelayState":"","SAMLResponse":saml}, headers = headers)

  r4 = s2.get("https://www.vklass.se/")
  return s2

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError ("Type %s not serializable" % type(obj))

def dateFromString(manad):
  manader = {
	"januari":1,
	"februari":2,
	"mars":3,
	"april":4,
        "maj":5,
        "juni":6,
        "juli":7,
        "augusti":8,
        "september":9,
        "oktober":10,
        "november":11,
        "december":12
	}
  try:
    return manader[manad]
  except:
    return 1

def getNarvaro(s,id):
  r5 = s.get("https://www.vklass.se/statistics/attendanceDetailed.aspx?userUID="+id)
  lista = []
  for data in r5.text.split("_manualCloseButtonText"):
    row = data.split('"text"')[1].split('}')[0]
    if row.__contains__("Status:"):
      rowdata = json.loads(row[1:])
      """Måndag 12 december 2022<br />kl: 10:45 - 11:40<br />Kurs: Matematik 1a <br />Status: Närvarande<br /><span style="color: red;">Sen ankomst:: 5 min</span>"""
      info = rowdata.split("<br />")
      date = info[0].split(" ")
      time = info[1].replace("kl: ","").split(" - ")
      hhmm = time[0].split(":")
      ehhmm = time[1].split(":")
      start = datetime(int(date[3]), dateFromString(date[2]), int(date[1]),int(hhmm[0]),int(hhmm[1]))
      end = datetime(int(date[3]), dateFromString(date[2]), int(date[1]),int(ehhmm[0]),int(ehhmm[1]))
      lektion = info[2].replace("Kurs: ","").strip()
      status = info[3].replace("Status: ","").strip()
      avvikelse = 0
      if len(info) == 5:
        avvikelse = int(info[4].split(">")[1].split("<")[0].split(":")[-1].strip().split(" ")[0])
      narvaro_entry = {
        "start":start,
        "end":end,
        "lektion":lektion,
        "status":status,
        "avvikelse": avvikelse
      }
      lista.append(narvaro_entry)
  return sorted(lista,key=itemgetter('start'))

def getKlass(s):
  r5 = s.get("https://www.vklass.se/Class.aspx")
  elever = []
  for data in r5.text.split("teacherStudentLink"):
    row = data.split('Info & resultat')[0]
    if row.__contains__('href="/User.aspx?id='):
      id_and_name = row.split("id=")[1].split('">')
      student = {
        "short_id":id_and_name[0],
        "name":id_and_name[1].split("</a>")[0],
        "uuid":row.split('/Results/StudentResult.aspx?id=')[1].split("&amp;")[0]
      }
      elever.append(student)
  return elever

if __name__ == "__main__":
  from docopt import docopt
  args = docopt(__doc__)

  if args["<action>"] == "narvaro":
    print(getNarvaro(login(args["<username>"],args["<password>"]),"e5903f64-c3f9-45ad-94d3-36cefa481484"))

  if args["<action>"] == "elever":
    print(getKlass(login(args["<username>"],args["<password>"])))

  if args["<action>"] == "narvaroklass":
    data = []
    s = login(args["<username>"],args["<password>"])
    for elev in getKlass(s):
      elev["narvaro"] = getNarvaro(s,elev["uuid"])
      data.append(elev)
      print(json.dumps(data, default=json_serial))


