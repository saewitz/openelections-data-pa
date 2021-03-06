import requests
import csv
from bs4 import BeautifulSoup

election_id = '53'
county = 'Monroe'

results = []

url = "http://agencies.monroecountypa.gov/elections/"
r = requests.get(url)
soup = BeautifulSoup(r.text, "html.parser")

offices = [
    'Presidential Electors', 'Attorney General', 'Auditor General', 'State Treasurer', 'Representative in Congress 7th District', 'Representative in Congress 8th District', 'Representative in the General Assembly 115th District',
    'Representative in the General Assembly 176th District', 'Representative in the General Assembly 189th District'
]

#for el in soup.find_all('h4', attrs={'class':'panel-title'}):
#    if el.find('a'):
#        if 'Delegate' not in el.find('a').text.strip():
#            offices.append(el.find('a').text.strip())

all_office_ids = [x['value'] for x in soup.find_all('button', attrs={'class':'btn btn-warning btnCandPrecincts'})]
office_ids = []

for index, element in enumerate(all_office_ids):
    if index % 2 == 0:
        office_ids.append(element)

office_ids = all_office_ids[0:len(offices)]

offices_with_ids = zip(offices, office_ids)

for office, office_id in offices_with_ids:
    print(office)
    url = f"http://agencies.monroecountypa.gov/elections/getData.ashx?partyname= &electionid={election_id}&el_off_id={office_id}&type=precinct"
#    dem_url = f"http://agencies.monroecountypa.gov/elections/getData.ashx?partyname=DEMOCRATIC&electionid={election_id}&el_off_id={office_id}&type=precinct"
#    rep_url = f"http://agencies.monroecountypa.gov/elections/getData.ashx?partyname=REPUBLICAN&electionid={election_id}&el_off_id={office_id}&type=precinct"
#    r = requests.get(dem_url)
#    for result in r.json():
#        results.append([county, result['precinctName'], office, None, 'DEM', result['firstName']+ ' '+ result['lastName'], result['totalVotes']])
    r = requests.get(url)
    for result in r.json():
        results.append([county, result['precinctName'], office, None, result['party'], result['firstName']+ ' '+ result['lastName'], result['totalVotes']])


with open('20201103__pa__general__monroe__precinct.csv', 'wt') as csvfile:
    w = csv.writer(csvfile)
    headers = ['county', 'precinct', 'office', 'district', 'party', 'candidate', 'votes']
    w.writerow(headers)
    w.writerows(results)
