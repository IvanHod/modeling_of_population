import sys
import logging as log
import os
from data_helper import DataHelper
from tools import *
from plot import Plot
import math


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
	factor_history = {}

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

	def calculate(self, from_file=False):
		if from_file:
			self.big_prediction, self.prediction, self.interval_prediction = self.data_helper.from_files()
		else:
			self.detect_factors()
			self.detect_female_factor()

			self.split_factors_by_year()
			self.calculate_prediction(write_xls=False)

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
		self.factor_history[5] = {'factors': factors}
		self.factors = factors

	def detect_female_factor(self):
		log.info('Detect of female factor...')

		count_children = union_count_genders(self.data[self.years[1]]['0-4'])

		self.female_factor['general'] = count_children / get_number_middle_female(self.data[self.years[0]])
		self.factor_history[5]['female'] = self.female_factor['general']

		self.detect_relation_male_vs_female()

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
				factors_interval_year[year] = self.factors[interval]
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
				next_children = number_children + female_factor * get_number_middle_female(last_year)
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

	def calculate_prediction(self, write_xls=False):
		log.info('Calculating of predictions...')
		titles = ['year'] + list(sorted(self.factors.keys(), key=lambda k: int(k.split('-')[0]))) + ['100+']
		data, data_by_year = {}, {2000: self.data[self.years[0]]}
		data_by_an_interval = split_interval(data_by_year[2000])
		prediction_data_by_an_interval = {
			2000: list(map(lambda x: int(union_count_genders(data_by_an_interval[x])), data_by_an_interval))
		}
		for year in self.data:
			data[year], data_by_year[year] = [], []
			for interval in sorted(self.data[year], key=lambda k: int(k.split('-')[0])):
				count = union_count_genders(self.data[year][interval])
				data[year].append(int(count))
				if year == self.years[0]:
					data_by_year[year].append(int(count))

		prediction_data_by_5 = self.modeling_by_5(data)
		prediction_data_by_year = self.modeling_by_1(data_by_year)
		self.split_factors_by_year()
		prediction_data_by_an_interval = self.modeling_by_1_interval_1(prediction_data_by_an_interval)

		if write_xls:
			self.data_helper.write_to_xls(titles, prediction_data_by_5, prediction_data_by_year, prediction_data_by_an_interval)

	def modeling_by_5(self, data):
		log.info('Calculating for 5 years...')
		fm = self.female_factor
		last_year = self.years[-1]
		for_prediction = self.data[last_year]
		for num in range(5, 101, 5):
			childs = self.female_factor['general'] * get_number_middle_female(for_prediction)
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
		log.info('Calculating for an year...')
		for_prediction = self.data[self.years[0]]
		for num in range(1, 101, 1):
			if num % 20 == 0:
				log.info('Calculating for an year in {} iteration...'.format(num))

			fm = self.female_factor
			number_children = .8 * union_count_genders(for_prediction['0-4'])
			children = number_children + self.female_factor_by_year * get_number_middle_female(for_prediction)
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

	def modeling_by_1_interval_1(self, data: dict)->dict:
		log.info('Calculating for an year and an year interval...')
		self.factor_history[1], start_year = [], 2000
		initial_year = {start_year: split_interval(self.data[start_year])}

		# factors, ff = {}, self.female_factor['general'] / 5
		factors, ff = {}, (self.female_factor['general'] * 2 / 1.325) / 5
		for interval in sorted(self.factors, key=lambda k: int(k.split('-')[0])):
			start = int(interval.split('-')[0])
			value = min(math.pow(self.factors[interval], 1 / 5), 1.0)
			for i in range(5):
				factors[start + i] = value
		self.factor_history[1].append({
			'female': ff,
			'factors': factors.copy()
		})

		for_prediction, fm = initial_year[start_year], self.female_factor
		for num in range(1, 501, 1):
			if num % 100 == 0:
				log.info('Calculating for an year and an interval in {} iteration...'.format(num))

			children = ff * get_number_middle_female_year(for_prediction)
			new_data = {0: {'male': children * fm['male'], 'female': children * fm['female']}}

			next_year = self.years[0] + num
			# log.info('{} - {} number of people.'.format(next_year, int(sum(union_count_genders(v) for v in for_prediction.values()))))
			data[next_year] = [int(children)]
			for interval in sorted(factors):
				new_data[interval + 1] = new_interval(for_prediction[interval], factors[interval])
				data[next_year].append(int(union_count_genders(new_data[interval + 1])))

			self.interval_prediction[next_year] = new_data
			for_prediction = new_data
			
		return data


if __name__ == '__main__':
	formater = u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s'
	log.basicConfig(format=formater, level=log.DEBUG)

	main = Main()
	main.read_data()
	main.calculate(from_file=False)

	folder = 'mixed'

	plot = Plot(main)
	# plot.draw_factors("Коэффициенты \"выживаемости\"", "Возрастные интервалы", "Коэффициэнты")
	plot.draw_by_year("График населения", "Возрастные интервалы", "Кол-во населения")
	# plot.draw_compare('{}_by_interval'.format(folder), "График населения на {}", "Возрастные интервалы",
	#                   "Кол-во населения")
	plot.draw_factors_new("Коэффициенты \"выживаемости\"", "Возрастные интервалы", "Коэффициэнты")
	plot.draw_compare_with_interval('{}_by_interval'.format(folder), "График населения на {}", "Возрастные интервалы",
	                  "Кол-во населения")

	sys.exit()
