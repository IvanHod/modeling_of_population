import sys
import logging as log
import os
from data_helper import DataHelper


class Main:
	data_helper = None
	data = {}
	factors = {}
	female_factor = {'general': 0, 'male': 0, 'female': 0}
	factors_by_year = {}

	def __init__(self, country='Russian Federation', years=None):
		if years and len(years) != 2:
			raise Exception("Must be two years...")

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
		factors = {}
		step = 4
		for rn in range(0, 101, 5):
			next_rn = rn + 5
			interval = '{}-{}'.format(rn, rn + step)
			next_interval = '{}-{}'.format(next_rn, next_rn + step)
			prev_year = self.data[self.years[0]][interval]
			if prev_year:
				if next_interval in self.data[self.years[1]]:
					next_year = self.data[self.years[1]][next_interval]
					prev_year_number = prev_year['male'] + prev_year['female']
					next_year_number = next_year['male'] + next_year['female']
					factors[interval] = next_year_number / prev_year_number
			else:
				raise Exception('There is not interval {} for an year {}'.format(interval, self.years[0]))
		self.factors = factors

	def detect_female_factor(self):
		log.info('Detect of female factor...')
		step = 4
		ranges = range(20, 40, 5)
		count_woman = 0
		for rn in ranges:
			interval = '{}-{}'.format(rn, rn + step)
			count_woman += self.data[self.years[0]][interval]['female']

		children_interval = self.data[self.years[0]]['0-4']
		count_children = children_interval['female'] + children_interval['male']

		self.female_factor['general'] = count_children / count_woman

		self.detect_relation_male_vs_female()

	def detect_relation_male_vs_female(self):
		log.info('Detect a relation birthday between male and female...')

		male_coefficient = 0
		for year in self.years:
			interval = self.data[year]['0-4']
			male_coefficient += interval['male'] / (interval['male'] + interval['female'])

		male_coefficient /= 2
		self.female_factor['male'] = self.female_factor['general'] * male_coefficient
		self.female_factor['female'] = self.female_factor['general'] - self.female_factor['male']

	def split_factors_by_year(self):
		log.info('Translate factors by a year step...')
		self.factors_by_year = {}


if __name__ == '__main__':

	formater = u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s'
	log.basicConfig(format=formater, level=log.DEBUG)

	main = Main()
	main.read_data()

	main.detect_factors()
	main.detect_female_factor()

	sys.exit()
