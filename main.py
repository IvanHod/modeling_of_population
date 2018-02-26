import sys
import logging as log
import os
from data_helper import DataHelper


class Main:

	data_helper = None
	data = {}
	factors = {}
	factors_by_year = {}
	femail_factor = None
	relaction_male_vs_female = None

	def __init__(self, country='Russian Federation', years=None):
		if years is None:
			years = [2000, 2005]

		self.country = country
		self.years = years
		for year in years:
			self.data[year] = {}

		self.data_helper = DataHelper(country, years)

	def read_data(self):
		log.info('Reading of data...')
		if os.path.exists(self.data_helper.csv_file):
			self.data = self.data_helper.read_csv()
		else:
			self.data = self.data_helper.read_xls()
			self.data_helper.xls_to_csv(self.data)

	def detect_factors(self):
		log.info('Detect of factors...')
		self.factors = {}

	def detect_femail_factor(self):
		log.info('Detect of femail factor...')
		self.femail_factor = None

	def detect_relation_male_vs_female(self):
		log.info('Detect a relation birthday between male and femail...')
		self.relaction_male_vs_female = None

	def split_factors_by_year(self):
		log.info('Translate factors by a year step...')
		self.factors_by_year = {}


if __name__ == '__main__':

	formater = u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s'
	log.basicConfig(format=formater, level=log.DEBUG)

	main = Main()
	main.read_data()

	main.detect_factors()

	sys.exit()
