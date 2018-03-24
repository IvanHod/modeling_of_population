import sys
import logging as log
import os
from data_helper import DataHelper
import math


class Main:
	data_helper = None
	data = {}
	factors = {}
	female_factor = {'general': 0, 'male': 0, 'female': 0}
	female_factor_by_year = None
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

		children_interval = self.data[self.years[1]]['0-4']
		count_children = children_interval['female'] + children_interval['male']

		self.female_factor['general'] = count_children / self.get_number_middle_female(self.data[self.years[0]])

		self.detect_relation_male_vs_female()

	def get_number_middle_female(self, year, delimiter=None):
		count_woman = 0
		for rn in range(20, 40, 5):
			interval = '{}-{}'.format(rn, rn + 4)
			count_woman += year[interval]['female']
		if delimiter:
			count_woman /= delimiter
		return count_woman

	def detect_relation_male_vs_female(self):
		log.info('Detect a relation birthday between male and female...')

		male_coefficient = 0
		for year in self.years:
			interval = self.data[year]['0-4']
			male_coefficient += interval['male'] / (interval['male'] + interval['female'])

		male_coefficient /= len(self.years)
		self.female_factor['male'] = male_coefficient
		self.female_factor['female'] = 1 - self.female_factor['male']

	def split_factors_by_year(self):
		log.info('Translate factors by a year step...')
		factors_by_year = {}
		for interval in self.factors:
			factors_by_year[interval] = self.factors[interval] / 5

		self.factors_by_year = factors_by_year
		self.female_factor_by_year = self.female_factor['general'] / 5

	def calculate_prediction(self):
		titles = ['year'] + list(sorted(self.factors.keys(), key=lambda k: int(k.split('-')[0]))) + ['100+']
		data = {}
		data_by_year = {2000: self.data[self.years[0]]}
		for year in self.data:
			data[year] = []
			data_by_year[year] = []
			for interval in sorted(self.data[year], key=lambda k: int(k.split('-')[0])):
				count = self.data[year][interval]['male'] + self.data[year][interval]['female']
				data[year].append(int(count))
				if year == self.years[0]:
					data_by_year[year].append(int(count))

		last_year = self.years[-1]
		for_prediction = self.data[last_year]
		for num in range(5, 101, 5):
			childs = self.female_factor['general'] * self.get_number_middle_female(for_prediction)
			new_data = {'0-4': {
				'male': childs * self.female_factor['male'],
				'female': childs * self.female_factor['female']
			}}
			last_year = self.years[-1] + num
			data[last_year] = [int(childs)]
			for interval in sorted(self.factors, key=lambda k: int(k.split('-')[0])):
				number = for_prediction[interval]
				next_interval = self.next_interval(interval)
				new_data[next_interval] = {
					'male': number['male'] * self.factors[interval],
					'female': number['female'] * self.factors[interval]
				}
				data[last_year].append(int((number['male'] + number['female']) * self.factors[interval]))

			for_prediction = new_data

		year = self.years[0]
		for_prediction = self.data[year]
		female_factor = self.female_factor_by_year
		for num in range(1, 101, 1):
			number_children = for_prediction['0-4']['male'] + for_prediction['0-4']['female']
			next_children = number_children * .8 + female_factor * self.get_number_middle_female(for_prediction)
			new_data = {'0-4': {
				'male': next_children * self.female_factor['male'],
				'female': next_children * self.female_factor['female']
			}}

			next_year = self.years[0] + num
			data_by_year[next_year] = [int(next_children)]
			for interval in sorted(self.factors_by_year, key=lambda k: int(k.split('-')[0])):
				next_interval = self.next_interval(interval)
				number = for_prediction[interval]
				next_number = for_prediction[next_interval]['male'] + for_prediction[next_interval]['female']
				factor = self.factors_by_year[interval]
				new_data[next_interval] = {
					'male': next_number * .8 * self.female_factor['male'] + number['male'] * factor,
					'female': next_number * .8 * self.female_factor['female'] + number['female'] * factor
				}
				value = int(new_data[next_interval]['male'] + new_data[next_interval]['female'])
				data_by_year[next_year].append(value)

			year = next_year
			for_prediction = new_data

		self.data_helper.write_to_xls(titles, data, data_by_year)

	def next_interval(self, interval: str):
		numbers = list(map(lambda x: int(x), interval.split('-')))
		return '{}-{}'.format(numbers[0] + 5, numbers[1] + 5)


if __name__ == '__main__':

	formater = u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s'
	log.basicConfig(format=formater, level=log.DEBUG)

	main = Main()
	main.read_data()

	main.detect_factors()
	main.detect_female_factor()

	main.split_factors_by_year()

	main.calculate_prediction()

	sys.exit()
