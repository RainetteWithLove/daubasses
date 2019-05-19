import requests
import re
import os
from bs4 import BeautifulSoup

USERNAME = 'XXXXX'
PASSWORD = 'XXXXX'

MONTHS = {
	'Janvier':'01',
	'Février':'02',
	'Mars':'03',
	'Avril':'04',
	'Mai':'05',
	'Juin':'06',
	'Juillet':'07',
	'Août':'08',
	'Septembre':'09',
	'Octobre':'10',
	'Novembre':'11',
	'Décembre':'12'
}


class Daubasses():
	URL = 'https://www.daubasses.com'
	LOGIN_URL = '/mon-compte'
	LETTRES_URL = '/zone-premium/lettres-boursieres'
	DESTINATION = 'lettres'

	def __init__(self, username, password):
		self.create_session()
		self.username = username
		self.password = password

	def create_session(self):
		user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Brave Chrome/74.0.3729.131 Safari/537.36'
		self.session = requests.session()
		self.session.headers.update({'User-Agent': user_agent})

	def login(self):
		url = self.URL + self.LOGIN_URL
		r = self.session.get(url)

		soup = BeautifulSoup(r.content, 'html.parser')
		# Login protected by 2 tokens :
		#	- nb 1, standard : <input type="hidden" name="return" value="aW5kZXgucGhwP0l0ZW1pZD0xNzA=" />
		#	- nb 2, vicious : <input type="hidden" name="39c8dfac2f446a7927b508761e4aadca" value="1" />
		# quick info : seems to be powered by joomla
		token_1 = soup.find(attrs={"name": "return"})["value"]
		token_2 = soup.find(attrs={'type': 'hidden', 'value': '1'})['name']

		params = {'username': self.username,
				'password': self.password, 
				'Submit': 'Connexion',
				'option': 'com_users',
				'task': 'user.login',
				'return': token_1,
				token_2: '1'
				}

		r = self.session.post(url, data=params)


	def get_lettres(self):
		url = self.URL + self.LETTRES_URL
		r = self.session.get(url)
		soup = BeautifulSoup(r.content, 'html.parser')

		links = {}
		for balise in soup.find_all('td', attrs={'class': 'list-title'}):
			link = balise.a.get('href')
			year = re.sub('[^0-9]+', '', balise.a.text)
			links.update({year: link})
		
		links.pop('', None) # Delete false positiv result

		pdfs = {}
		for year, link in links.items():
			url = self.URL + link
			r = self.session.get(url)
			soup = BeautifulSoup(r.content, 'html.parser')
			tmp = soup.find('div', attrs={'class': 'item-page'})
			for pdf in tmp.find_all('a'):
				month = pdf.text.split(' ')[0]
				if month is not '':
					date = year + '-' + MONTHS[month]
					url =self.URL + pdf.get('href')
					pdfs.update({date: url})

		print(f'Links crawler finished, {len(pdfs)} lettres boursieres found!')

		data_dir = os.path.join(os.getcwd(), self.DESTINATION)
		if not os.path.exists(data_dir):
			os.makedirs(data_dir)

		print(f'Starting download...')

		counter = 0
		for date, url in pdfs.items():
			counter += 1
			print(f'Getting pdf {counter} over {len(pdfs)}')
			r = self.session.get(url, stream=True)
			with open(os.path.join(os.getcwd(), self.DESTINATION, date + '.pdf'), 'wb') as f:
				f.write(r.content)
			f.close()


def main():
	crawler = Daubasses(USERNAME, PASSWORD)
	crawler.login()
	crawler.get_lettres()

if __name__ == '__main__':
	main()
