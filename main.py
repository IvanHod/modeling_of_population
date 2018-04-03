import sys
import logging as log
import os
from data_helper import DataHelper
from plot import Plot


def union_count_genders(count):
	return count['male'] + count['female']


def get_next_interval(interval: str):
	numbers = list(map(lambda x: int(x), interval.split('-')))
	return '{}-{}'.format(numbers[0] + 5, numbers[1] + 5)


def get_prev_interval(interval: str):
	numbers = list(map(lambda x: int(x), interval.split('-')))
	return '{}-{}'.format(numbers[0] - 5, numbers[1] - 5)


class Main:
	data_helper = None
	data = {}
	prediction = {}
	big_prediction = {}
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
		# factors_by_year = self.factors
		factors_by_year = {}
		for interval in self.factors:
			factors_by_year[interval] = self.factors[interval] / 5
		self.factors_by_year = factors_by_year

		# self.female_factor_by_year = self.female_factor['general']
		self.female_factor_by_year = self.female_factor['general'] / 5
		self.corrected_factors_by_year()

	def corrected_factors_by_year(self):
		data_last_year = self.data[self.years[-1]]
		year, female_factor = self.years[0], self.female_factor_by_year
		male_percent, female_percent = self.female_factor['male'], self.female_factor['female']
		factors = self.factors_by_year
		eps, step = 30, .0002
		while True:
			last_year = self.data[year]
			for i in range(1, 6):
				number_children = .8 * union_count_genders(last_year['0-4'])
				next_children = number_children + female_factor * self.get_number_middle_female(last_year)
				# next_children = female_factor * self.get_number_middle_female(last_year)
				new_data = {'0-4': {
					'male': next_children * male_percent,
					'female': next_children * female_percent
				}}

				for interval in sorted(factors, key=lambda k: int(k.split('-')[0])):
					next_interval = get_next_interval(interval)
					number, next_number = last_year[interval], .8 * union_count_genders(last_year[next_interval])
					new_data[next_interval] = {
						'male': next_number * male_percent + number['male'] * factors[interval],
						'female': next_number * female_percent + number['female'] * factors[interval]
						# 'male': number['male'] * factors[interval],
						# 'female': number['female'] * factors[interval]
					}

				last_year = new_data

			is_end = True
			for interval in sorted(factors.keys(), key=lambda k: int(k.split('-')[0])):
				perfect_value = union_count_genders(data_last_year[interval])
				predicate_value = union_count_genders(last_year[interval])
				diff = predicate_value - perfect_value
				if abs(diff) > eps:
					is_end = False
					if interval == '0-4':
						female_factor += -1 * step if diff > 0 else step
					else:
						factors[get_prev_interval(interval)] += -1 * step if diff > 0 else step

			if is_end:
				self.factors_by_year = factors
				self.female_factor_by_year = female_factor
				break

	def calculate_prediction(self, write_xls=False):
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
				next_interval = get_next_interval(interval)
				new_data[next_interval] = {
					'male': number['male'] * self.factors[interval],
					'female': number['female'] * self.factors[interval]
				}
				data[last_year].append(int((number['male'] + number['female']) * self.factors[interval]))

			self.big_prediction[last_year] = new_data
			for_prediction = new_data

		for_prediction = self.data[self.years[0]]
		female_factor = self.female_factor_by_year
		for num in range(1, 101, 1):
			number_children = union_count_genders(for_prediction['0-4'])
			next_children = number_children * .8 + female_factor * self.get_number_middle_female(for_prediction)
			# next_children = female_factor * self.get_number_middle_female(for_prediction)
			new_data = {'0-4': {
				'male': next_children * self.female_factor['male'],
				'female': next_children * self.female_factor['female']
			}}

			next_year = self.years[0] + num
			data_by_year[next_year] = [int(next_children)]
			for interval in sorted(self.factors_by_year, key=lambda k: int(k.split('-')[0])):
				next_interval = get_next_interval(interval)
				number = for_prediction[interval]
				factor = self.factors_by_year[interval]
				new_data[next_interval] = {
					'male': .8 * for_prediction[next_interval]['male'] + number['male'] * factor,
					'female': .8 * for_prediction[next_interval]['female'] + number['female'] * factor
					# 'male': number['male'] * factor,
					# 'female': number['female'] * factor
				}
				value = int(new_data[next_interval]['male'] + new_data[next_interval]['female'])
				data_by_year[next_year].append(value)

			self.prediction[next_year] = new_data
			for_prediction = new_data

		if write_xls:
			self.data_helper.write_to_xls(titles, data, data_by_year)


if __name__ == '__main__':

	formater = u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s'
	log.basicConfig(format=formater, level=log.DEBUG)

	main = Main()
	main.read_data()

	main.detect_factors()
	main.detect_female_factor()

	main.split_factors_by_year()

	main.calculate_prediction(write_xls=True)

	plot = Plot(main)
	# plot.draw_factors("Коэффициенты \"выживаемости\"", "Возрастные интервалы", "Коэффициэнты")
	# plot.draw_by_year("График населения", "Возрастные интервалы", "Кол-во населения")
	plot.draw_compare("График населения на 2050", "Возрастные интервалы", "Кол-во населения")

	sys.exit()
