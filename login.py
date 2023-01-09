"""
vklass cli

Usage:
  vklass <action> <username> <password>
"""
import requests
import json
from datetime import datetime, date
from docopt import docopt
args = docopt(__doc__)

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
user = args["<username>"]
pwd = args["<password>"]

s = requests.Session()

r = s.get('https://auth.vklass.se/saml/initiate?idp=https%3A%2F%2Fauth.goteborg.se%2Fidp%2Fsps%2Fskola%2Fsaml20&org=189', headers = headers)
#print(r.status_code)
#print(r.content)
#print(requests.utils.dict_from_cookiejar(s.cookies))

headers["Host"] = "auth.goteborg.se"
headers["Origin"] = "https://auth.goteborg.se"
headers["Referer"] = "https://auth.goteborg.se/auth/login"
cookie_obj = requests.cookies.create_cookie(name="WASReqURL",value="http:///auth/Responder")
s.cookies.set_cookie(cookie_obj)

r2 = s.post('https://auth.goteborg.se/auth/j_security_check', data={'j_username':user,'j_password':pwd,'pw':'','login':'Logga in'}, headers = headers)
#print(r2.status_code)
#print(r2.content)
if r2.text.__contains__('name="SAMLResponse" value="'):
  saml = r2.text.split('name="SAMLResponse" value="')[1].split('"')[0]
else:
  print("Fel lösenord / användarnamn")
  exit()

headers["Origin"] = "https://auth.goteborg.se"
headers["Referer"] = "https://auth.goteborg.se/"

#print(requests.utils.dict_from_cookiejar(s.cookies))

kakor = requests.utils.dict_from_cookiejar(s.cookies)
kakorlogin = {
	"saml-session":kakor["saml-session"],
	"_tpc_persistance_cookie":kakor["_tpc_persistance_cookie"],
        "BBN01b9bc29":kakor["BBN01b9bc29"],
}
#print("\n\n")
#print(kakorlogin)

s2 = requests.Session()
requests.utils.add_dict_to_cookiejar(s2.cookies,kakorlogin)
#print({"RelayState":"","SAMLResponse":saml})
headers["Host"] = "auth.vklass.se"
r3 = s2.post('https://auth.vklass.se/saml/assertion', data={"RelayState":"","SAMLResponse":saml}, headers = headers)
#print(r3.request.headers)
#print(r3.content)
#print(requests.utils.dict_from_cookiejar(s2.cookies))

r4 = s2.get("https://www.vklass.se/")
#print(r4.content)

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError ("Type %s not serializable" % type(obj))


def getNarvaro(id):
  r5 = s2.get("https://www.vklass.se/statistics/attendanceDetailed.aspx?userUID="+id)
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
      start = datetime(int(date[3]), 12, int(date[1]),int(hhmm[0]),int(hhmm[1]))
      end = datetime(int(date[3]), 12, int(date[1]),int(ehhmm[0]),int(ehhmm[1]))
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
  return lista

def getKlass():
  r5 = s2.get("https://www.vklass.se/Class.aspx")
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

if args["<action>"] == "narvaro":
  print(getNarvaro("e5903f64-c3f9-45ad-94d3-36cefa481484"))

if args["<action>"] == "elever":
  print(getKlass())

if args["<action>"] == "narvaroklass":
  data = []
  for elev in getKlass():
    elev["narvaro"] = getNarvaro(elev["uuid"])
    data.append(elev)
  print(json.dumps(data, default=json_serial))

