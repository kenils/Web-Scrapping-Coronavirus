import requests #Importing module to send API Requests
import json #To Access the scrapped data
import pyttsx3  #Stands for Python Text to Speech
import speech_recognition as sr 
import re
import threading #Importing Threading for parallel processing to check whether data is udpated
import time 

#Private Keys to access the Parse Hub API
API_KEY = "t_Hc1Ga4afkj"         
PROJECT_TOKEN = "tnU7hGfk23Bgft"
RUN_TOKEN = "tPFHV-gUQC-5"


class Data:
	def __init__(self, api_key, project_token):
		self.api_key = api_key
		self.project_token = project_token
		self.params = {
			"api_key": self.api_key
		}
		self.data = self.get_data()

	def get_data(self):
		response = requests.get(f'https://www.parsehub.com/api/v2/projects/{self.project_token}/last_ready_run/data', params=self.params)
		data = json.loads(response.text)
		return data

	def get_total_cases(self):
		data = self.data['total'] 

		for content in data:
			if content['name'] == "Coronavirus Cases:":
				return content['value']

	def get_total_deaths(self):
		data = self.data['total']

		for content in data:
			if content['name'] == "Deaths:":
				return content['value']

		return "0"

	def get_country_data(self, country): 
		data = self.data["country"]

		for content in data:
			if content['name'].lower() == country.lower():
				return content

		return "0"

	def get_list_of_countries(self):
		countries = []
		for country in self.data['country']:
			countries.append(country['name'].lower()) 

		return countries

	def update_data(self):
		response = requests.post(f'https://www.parsehub.com/api/v2/projects/{self.project_token}/run', params=self.params) #api request to get data

		def poll():
			time.sleep(0.1) #Sleep for 0.1 sec and let other threads take over
			old_data = self.data
			while True:
				new_data = self.get_data() 
				if new_data != old_data:
					self.data = new_data
					print("Data updated")
					break
				time.sleep(5) #Sleep after 5 sec


		t = threading.Thread(target=poll)
		t.start()


def speak(text):
	engine = pyttsx3.init() #Initialize the search engine
	engine.say(text)        
	engine.runAndWait() 


def get_audio():
	r = sr.Recognizer() 
	with sr.Microphone() as source:
		audio = r.listen(source)
		said = ""

		try:
			said = r.recognize_google(audio)
		except Exception as e:
			print("Exception:", str(e))

	return said.lower()


def main():
	print("Started Program")
	data = Data(API_KEY, PROJECT_TOKEN)
	END_PHRASE = "stop" #Say stop to quit listening
	country_list = data.get_list_of_countries() 

	TOTAL_PATTERNS = {
					re.compile("[\w\s]+ total [\w\s]+ cases"):data.get_total_cases,
					re.compile("[\w\s]+ total cases"): data.get_total_cases,
                    re.compile("[\w\s]+ total [\w\s]+ deaths"): data.get_total_deaths,
                    re.compile("[\w\s]+ total deaths"): data.get_total_deaths
					} #Dictionary of patterns to check for requried words

	COUNTRY_PATTERNS = {
					re.compile("[\w\s]+ cases [\w\s]+"): lambda country: data.get_country_data(country)['total_cases'],
                    re.compile("[\w\s]+ deaths [\w\s]+"): lambda country: data.get_country_data(country)['total_deaths'],
					} #Dictionary of patterns to check for requried words

	UPDATE_COMMAND = "update"

	while True:
		print("Listening...")
		text = get_audio()
		print(text)
		result = None

		for pattern, func in COUNTRY_PATTERNS.items():
			if pattern.match(text):
				words = set(text.split(" "))
				for country in country_list: #Check if country is present in list
					if country in words:
						result = func(country)
						break

		for pattern, func in TOTAL_PATTERNS.items():
			if pattern.match(text):
				result = func()
				break

		if text == UPDATE_COMMAND:
			result = "Data is being updated. This may take a moment!"
			data.update_data()

		if result:
			speak(result)

		if text.find(END_PHRASE) != -1:  # Break loop
			print("Exit")
			break

main()
