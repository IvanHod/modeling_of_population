import sys
import logging as log
import os
from data_helper import DataHelper
import random
from scipy import interpolate
import numpy as np


def union_count_genders(count):
	return count['male'] + count['female']

def get_next_interval(interval: str):
	numbers = list(map(lambda x: int(x), interval.split('-')))
	return '{}-{}'.format(numbers[0] + 5, numbers[1] + 5)

def get_prev_interval(interval: str):
	numbers = list(map(lambda x: int(x), interval.split('-')))
	return '{}-{}'.format(numbers[0] - 5, numbers[1] - 5)


def new_interval(number: dict, factor, rest=None) -> dict:
	_new_interval = {
		'male': number['male'] * factor,
		'female': number['female'] * factor
	}
	if rest:
		_new_interval['male'] += .8 * rest['male']
		_new_interval['female'] += .8 * rest['female']
	return _new_interval

def get_number_middle_female_year(year, delimiter=None):
	count_woman = 0
	for rn in range(20, 41, 1):
		count_woman += year[rn]['female']
	if delimiter:
		count_woman /= delimiter
	return count_woman

# надо сделать разделение по полу
def interpolate_intervals(x, interval_1, interval_2):
	f_p = union_count_genders(interval_1)
	s_p = union_count_genders(interval_2)
	diff = (s_p - f_p) / 2
	f = interpolate.interp1d(x, [(f_p - diff) / 5, (s_p - diff) / 5])

	return f(range(x[0], x[0] + 4))


class Main:
	data_helper = None
	data = {}
	prediction = {}
	big_prediction = {}
	interval_prediction = {}
	factors = {}
	female_factor = {'general': 0, 'male': 0, 'female': 0}
	female_factor_by_year = None
	factors_by_year = {}
	factors_interval_year = {}

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
		factors_interval_year = {}
		for interval in self.factors:
			factors_by_year[interval] = self.factors[interval] / 5
			years = list(map(lambda i: int(i), interval.split('-')))
			for year in range(years[0], years[1] + 1):
				factors_interval_year[year] = self.factors[interval] / 5
		self.factors_by_year = factors_by_year
		self.factors_interval_year = factors_interval_year

		# self.female_factor_by_year = self.female_factor['general']
		self.female_factor_by_year = self.female_factor['general'] / 5
		self.corrected_factors_by_year()

	def corrected_factors_by_year(self, count=6, initial_year=None, data_last_year=None):
		if not data_last_year:
			data_last_year = self.data[self.years[-1]]
		year, female_factor = self.years[0], self.female_factor_by_year
		male_percent, female_percent = self.female_factor['male'], self.female_factor['female']
		factors = self.factors_by_year
		eps, step = 100, .0002
		while True:
			last_year = initial_year if initial_year else self.data[year]
			for i in range(1, count):
				number_children = .8 * union_count_genders(last_year['0-4'])
				next_children = number_children + female_factor * self.get_number_middle_female(last_year)
				new_data = {'0-4': {'male': next_children * male_percent, 'female': next_children * female_percent}}

				for interval in sorted(factors, key=lambda k: int(k.split('-')[0])):
					next_interval = get_next_interval(interval)
					new_data[next_interval] = new_interval(last_year[interval], factors[interval], last_year[next_interval])

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

	def corrected_factors_interval_year(self, initial_year, count=6, data_last_year=None):
		if not data_last_year:
			data_last_year = self.data[self.years[-1]]
		year, female_factor = self.years[0], self.female_factor_by_year
		male_percent, female_percent = self.female_factor['male'], self.female_factor['female']
		factors = self.factors_interval_year
		eps, step = 100, .0002
		while True:
			last_year = initial_year
			for i in range(1, count):
				children = female_factor * get_number_middle_female_year(last_year)
				new_data = {0: {'male': children * male_percent, 'female': children * female_percent}}

				for interval in sorted(factors):
					next_interval = interval + 1
					new_data[next_interval] = new_interval(last_year[interval], factors[interval], last_year[next_interval])

				last_year = new_data

			is_end = True
			for index in range(0, 100, 5):
				perfect_value = union_count_genders(data_last_year['{}-{}'.format(index, index + 4)])
				predicate_value = 0
				for i in range(index, index + 5):
					predicate_value += union_count_genders(last_year[i])
				diff = predicate_value - perfect_value
				if abs(diff) > eps:
					is_end = False
					rn = random.randint(0, 4)
					if index == 0 and rn == 0:
						female_factor += -1 * step if diff > 0 else step
					else:
						factors[index + rn] += -1 * step if diff > 0 else step

			if is_end:
				self.factors_interval_year = factors
				self.female_factor_by_year = female_factor
				break

	def calculate_prediction(self, pr_year=2005, write_xls=False):
		log.info('Calculating of predictions...')
		titles = ['year'] + list(sorted(self.factors.keys(), key=lambda k: int(k.split('-')[0]))) + ['100+']
		data, data_by_year = {}, {2000: self.data[self.years[0]]}
		for year in self.data:
			data[year], data_by_year[year] = [], []
			for interval in sorted(self.data[year], key=lambda k: int(k.split('-')[0])):
				count = union_count_genders(self.data[year][interval])
				data[year].append(int(count))
				if year == self.years[0]:
					data_by_year[year].append(int(count))

		data = self.modeling_by_5(data)
		interval_data = data_by_year
		data_by_year = self.modeling_by_1(data_by_year)
		data_by_year_interval_year = self.modeling_by_1_interval_1(interval_data)

		if write_xls:
			self.data_helper.write_to_xls(titles, data, data_by_year)

	def modeling_by_5(self, data):
		fm = self.female_factor
		last_year = self.years[-1]
		for_prediction = self.data[last_year]
		for num in range(5, 101, 5):
			childs = self.female_factor['general'] * self.get_number_middle_female(for_prediction)
			new_data = {'0-4': {'male': childs * fm['male'], 'female': childs * fm['female']}}

			last_year = self.years[-1] + num
			data[last_year] = [int(childs)]
			for interval in sorted(self.factors, key=lambda k: int(k.split('-')[0])):
				next_interval = get_next_interval(interval)
				new_data[next_interval] = new_interval(for_prediction[interval], self.factors[interval])

				data[last_year].append(int(union_count_genders(for_prediction[interval]) * self.factors[interval]))

			self.big_prediction[last_year] = new_data
			for_prediction = new_data
		return data

	def modeling_by_1(self, data):
		fm, female_factor = self.female_factor, self.female_factor_by_year
		for_prediction = self.data[self.years[0]]
		for num in range(1, 101, 1):
			number_children = .8 * union_count_genders(for_prediction['0-4'])
			children = number_children + female_factor * self.get_number_middle_female(for_prediction)
			new_data = {'0-4': {'male': children * fm['male'], 'female': children * fm['female']}}

			next_year = self.years[0] + num
			data[next_year] = [int(children)]
			for interval in sorted(self.factors_by_year, key=lambda k: int(k.split('-')[0])):
				next_interval = get_next_interval(interval)
				factor = self.factors_by_year[interval]

				new_data[next_interval] = new_interval(for_prediction[interval], factor, for_prediction[next_interval])
				data[next_year].append(int(union_count_genders(new_data[next_interval])))

			self.prediction[next_year] = new_data
			for_prediction = new_data

			# if next_year % 5 == 0:
			# 	prediction = self.big_prediction[next_year + 5]
			# 	self.corrected_factors_by_year(count=6, initial_year=new_data, data_last_year=prediction)

		return data

	def modeling_by_1_interval_1(self, data):
		initial_year = {2000: {}}
		source_data = self.data[2000]
		for interval in source_data:
			years = list(map(lambda i: int(i), interval.split('-')))
			for year in range(years[0], years[1] + 1):
				initial_year[2000][year] = {
					'male': source_data[interval]['male'] / 5,
					'female': source_data[interval]['female'] / 5
				}

		self.corrected_factors_interval_year(initial_year[2000])
		fm, female_factor = self.female_factor, self.female_factor_by_year
		for_prediction = initial_year[2000]
		for num in range(1, 101, 1):
			children = female_factor * get_number_middle_female_year(for_prediction)
			new_data = {0: {'male': children * fm['male'], 'female': children * fm['female']}}

			next_year = self.years[0] + num
			data[next_year] = [int(children)]
			for interval in sorted(self.factors_interval_year):
				next_interval = interval + 1
				factor = self.factors_interval_year[interval]

				new_data[next_interval] = new_interval(for_prediction[interval], factor, for_prediction[next_interval])
				data[next_year].append(int(union_count_genders(new_data[next_interval])))

			self.interval_prediction[next_year] = new_data
			for_prediction = new_data

		return data


if __name__ == '__main__':
	formater = u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s'
	log.basicConfig(format=formater, level=log.DEBUG)

	main = Main()
	main.read_data()

	# interpolate.interp1d()
	# main.detect_factors()
	# main.detect_female_factor()
	#
	# main.split_factors_by_year()
	#
	# folder = 'mixed'
	# year = 2030
	# main.calculate_prediction(year)
	#
	# plot = Plot(main)
	# # plot.draw_factors("Коэффициенты \"выживаемости\"", "Возрастные интервалы", "Коэффициэнты")
	# # plot.draw_by_year("График населения", "Возрастные интервалы", "Кол-во населения")
	# plot.draw_compare('{}_only_factors'.format(folder), "График населения на {}", "Возрастные интервалы",
	#                   "Кол-во населения")
	# plot.draw_interval_year('')

	sys.exit()
