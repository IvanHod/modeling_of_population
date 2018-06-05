import sys
import logging as log
import os
from data_helper import DataHelper
from tools import *
from plot import Plot
import math
from SALib.sample import saltelli
from SALib.analyze import sobol
import numpy as np
import random


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
			male_coefficient += interval['male'] / union_count_genders(interval)

		male_coefficient /= len(self.years)
		self.female_factor['male'] = male_coefficient
		self.female_factor['female'] = 1 - self.female_factor['male']

	def split_factors_by_year(self):
		log.info('Translate factors by a year step...')
		# factors_by_year = self.factors
		factors_by_year = {}
		for interval in sorted(self.factors, key=lambda k: int(k.split('-')[0])):
			years = list(map(lambda i: int(i), interval.split('-')))
			for year in range(years[0], years[1] + 1):
				factors_by_year[year] = min(math.pow(self.factors[interval], 1 / 5), 1.0)
		self.factors_by_year = factors_by_year

		# self.female_factor_by_year = self.female_factor['general']
		self.female_factor_by_year = self.female_factor['general'] / 5

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
		self.split_factors_by_year()
		prediction_data_by_an_interval = self.modeling_by_1(prediction_data_by_an_interval)

		if write_xls:
			self.data_helper.write_to_xls(titles, prediction_data_by_5, prediction_data_by_an_interval)

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

	def modeling_by_1(self, data: dict) -> dict:
		# log.info('Calculating for an year and an year interval...')
		self.factor_history[1], start_year = [], 2000
		initial_year = {start_year: split_interval(self.data[start_year])}

		# factors, ff = self.factors_by_year, (self.female_factor['general'] * 2 / 1.325) / 5
		factors, ff = self.factors_by_year, self.female_factor_by_year

		for_prediction, fm = initial_year[start_year], self.female_factor
		for num in range(1, 101, 1):
			if num % 150 == 0:
				log.info('Calculating for an year and an interval in {} iteration...'.format(num))

			children = ff * get_number_middle_female_year(for_prediction)
			new_data = {0: {'male': children * fm['male'], 'female': children - children * fm['male']}}

			next_year = self.years[0] + num
			data[next_year] = [int(children)]
			for interval in sorted(factors):
				new_data[interval + 1] = new_interval(for_prediction[interval], factors[interval])
				data[next_year].append(int(union_count_genders(new_data[interval + 1])))

			self.interval_prediction[next_year] = new_data
			for_prediction = new_data

		return data

	def sensitivity_analysis(self):
		female, relation, factors = self.sensitivity_analysis_detect_intervals([15, 40, 90])
		factors_names = list(sorted(map(lambda k: 'factor_{}'.format(k), factors), key=lambda k: int(k[7])))
		problem = {
			'num_vars': len(factors) + 2,
			'names': ['female', 'relation'] + factors_names,
			'bounds': [[female['min'], female['max']],
			           [relation['min'], relation['max']]]
			          + list(map(lambda k: [factors[k]['min'], factors[k]['max']], sorted(factors.keys())))
		}

		param_values = saltelli.sample(problem, 100)
		for year in [2010, 2020, 2050, 2100]:
			Y = self.sensitivity_analysis_evaluate(param_values, year)

			Si = sobol.analyze(problem, Y, print_to_console=False)
			print("__________________ {} __________________".format(year))
			print("")
			print(Si['S1'])
			print("")

	def sensitivity_analysis_evaluate(self, param_values, year):
		Y = []
		for params in param_values:
			female, relation, factor_10, factor_40, factor_90 = params
			res = self.sensitivity_analysis_model(female, relation, factor_10, factor_40, factor_90, year)
			Y.append(res)
		return np.array(Y)

	def sensitivity_analysis_model(self, female, relation, factor_10, factor_40, factor_90, year):
		data = {}
		self.female_factor_by_year = female
		self.female_factor['male'] = relation
		self.factors_by_year[10] = factor_10
		self.factors_by_year[40] = factor_40
		self.factors_by_year[90] = factor_90

		self.modeling_by_1(data)
		s = sum(map(lambda kv: union_count_genders(kv[1]), self.interval_prediction[year].items()))
		return s

	def sensitivity_analysis_detect_intervals(self, ages):
		rng = range(1950, 2006, 5)
		# rng = range(1995, 2006, 5)
		data = self.data_helper.read_xls(rng)
		female, relation, factors = {'min': 1, 'max': 0}, {'min': 1, 'max': 0}, {}
		for interval in ages:
			factors[interval] = {'min': 1, 'max': 0}
		for year in data:
			next_year, year_data = year + 5, data[year]
			new_relation = year_data['0-4']['male'] / union_count_genders(year_data['0-4'])
			relation['min'] = min(relation['min'], new_relation)
			relation['max'] = min(1.0, max(relation['max'], new_relation))

			if next_year in data:
				next_year_data = data[next_year]

				new_female = union_count_genders(next_year_data['0-4']) / get_number_middle_female(year_data)
				female['min'] = min(female['min'], new_female)
				female['max'] = min(1.0, max(female['max'], new_female))

				for i in ages:
					interval = '{}-{}'.format(i, i + 4)
					if get_next_interval(interval) in next_year_data and interval in year_data:
						new_factor = union_count_genders(
							next_year_data[get_next_interval(interval)]) / union_count_genders(year_data[interval])
						factors[i]['min'] = min(factors[i]['min'], new_factor)
						factors[i]['max'] = min(1.0, max(factors[i]['max'], new_factor))

		# transform factors by 1 year
		year_factors = {}
		# female['max'] = (female['max'] / 5) - 0.007
		female['max'] = (female['max'] / 5)
		female['min'] = female['min'] / 5
		for year in factors:
			year_factors[year] = {
				'max': min(math.pow(factors[year]['max'], 1 / 5), 1.0),
				'min': min(math.pow(factors[year]['min'], 1 / 5), 1.0)
			}
		print('................detected factors................')
		print(female)
		print(relation)
		print(year_factors)
		print('................detected factors................')
		return female, relation, year_factors

	def uncertainty_analysis(self):
		female, relation, f = self.sensitivity_analysis_detect_intervals([15, 40, 90])
		values = {}
		for year in range(2001, 2100):
			values[year] = []
		for i in range(1000):
			self.female_factor_by_year = random.uniform(female['min'], female['max'])
			self.female_factor['male'] = random.uniform(relation['min'], relation['max'])
			self.factors_by_year[15] = random.uniform(f[15]['min'], f[15]['max'])
			self.factors_by_year[40] = random.uniform(f[40]['min'], f[40]['max'])
			self.factors_by_year[90] = random.uniform(f[90]['min'], f[90]['max'])

			data = {}
			self.modeling_by_1(data)
			for year in range(2001, 2100):
				s = sum(map(lambda kv: union_count_genders(kv[1]), self.interval_prediction[year].items()))
				values[year].append(s)
		plot = Plot(main)
		plot.set_labels('Анализ неопределенности', 'Год', 'Популяция')
		plot.draw_uncertainty_analysis(values)


if __name__ == '__main__':
	formater = u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s'
	log.basicConfig(format=formater, level=log.DEBUG)

	main = Main()
	main.read_data()
	main.calculate(from_file=False)

	# main.sensitivity_analysis()

	main.uncertainty_analysis()

	# folder = 'mixed'
	#
	# # plot = Plot(main)
	# # # plot.draw_factors("Коэффициенты \"выживаемости\"", "Возрастные интервалы", "Коэффициэнты")
	# # plot.draw_by_year("График населения", "Возрастные интервалы", "Кол-во населения")
	# # # plot.draw_compare('{}_by_interval'.format(folder), "График населения на {}", "Возрастные интервалы",
	# # #                   "Кол-во населения")
	# # plot.draw_factors_new("Коэффициенты \"выживаемости\"", "Возрастные интервалы", "Коэффициэнты")
	# # plot.draw_compare_with_interval('{}_by_interval'.format(folder), "График населения на {}", "Возрастные интервалы",
	# #                   "Кол-во населения")

	sys.exit()
