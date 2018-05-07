import matplotlib.pyplot as plt
from tools import *
import logging as log


class Plot:

	def __init__(self, main):
		self.main = main
		self.intervals = list(sorted(main.factors.keys(), key=lambda k: int(k.split('-')[0])))

	def draw_factors(self, title, x_label, y_label):
		labels = list(sorted(self.main.factors, key=lambda k: int(k.split('-')[0])))
		ax = plt.subplot()
		for interval in labels:
			ax.bar([interval], [self.main.factors[interval]], color='b', alpha=.8)

		Plot.set_labels(title, x_label, y_label, )
		plt.show()

	def draw_factors_new(self, title, x_label, y_label):
		ax = plt.subplot()

		x, y = [], []
		factors_by_5 = self.main.factor_history[5]['factors']
		for interval in sorted(factors_by_5.keys(), key=lambda k: int(k.split('-')[0])):
			x.append(int(interval.split('-')[0]))
			y.append(factors_by_5[interval])

		ax.plot(x, y, 'o-b', alpha=.8, label='Факторы для 5 лет')
		x, y = [], []
		factors_by_1 = self.main.factor_history[1][0]['factors']
		for interval in factors_by_1.keys():
			x.append(int(interval))
			y.append(factors_by_1[interval])

		ax.plot(x, y, '.-g', alpha=.8, label='Факторы для каждого года')
		Plot.set_labels(title, x_label, y_label)
		plt.legend()
		plt.grid()
		plt.savefig('plots/factors/fig-start-factors.png')
		plt.clf()

	def draw_by_year(self, title, x_label, y_label):
		years = [2020, 2040, 2060, 2080, 2100]
		colors = {2020: 'y', 2040: 'g', 2060: 'c', 2080: 'b', 2100: 'r'}
		ax = plt.subplot()
		for year in years:
			show_legend, array = True, self.convert_to_plt(self.main.prediction, year)
			for el in array:
				if show_legend:
					ax.plot(el['keys'], el['values'], 'o-', alpha=.8, color=colors[year], label='Year {}'.format(year))
				else:
					ax.plot(el['keys'], el['values'], 'o-', alpha=.8, color=colors[year])
				show_legend = False
		plt.legend()
		Plot.set_labels(title, x_label, y_label)
		plt.show()

	def draw_compare(self, folder: str, title: str, x_label: str, y_label: str):
		for year in range(2010, 2051, 20):
			ax = plt.subplot()
			Plot.draw_prediction(ax, self.convert_to_plt(self.main.prediction, year), 'g', 'Прогнозирование по году')

			if year % 5 == 0:
				prediction = self.convert_to_plt(self.main.big_prediction, year)
				Plot.draw_prediction(ax, prediction, 'b', 'Прогнозирование по 5 годам')

				prediction = self.convert_to_plt(self.main.data_helper.get_prediction(year), year)
				Plot.draw_prediction(ax, prediction, 'r', 'Прогнозирование из xml')

			plt.legend()
			Plot.set_labels(title.format(year), x_label, y_label)
			plt.savefig('plots/{}/fig-{}.png'.format(folder, year))
			plt.clf()

	def draw_compare_with_interval(self, folder: str, title: str, x_label: str, y_label: str):
		for year in range(2100, 2101, 100):
			log.info('Render the plot for {} year...'.format(year))
			ax = plt.subplot()
			# x, y = [], []
			# for interval in sorted(self.main.prediction[year].keys(), key=lambda k: int(k.split('-')[0])):
			# 	x.append(int(interval.split('-')[0]))
			# 	y.append(union_count_genders(self.main.prediction[year][interval]))
			# ax.plot(x, y, 'g', label='Прогнозирование по году с интервалом в 5 лет')

			x, y = [], []
			for interval in self.main.interval_prediction[year].keys():
				x.append(int(interval))
				y.append(union_count_genders(self.main.interval_prediction[year][interval]))
			ax.plot(x, y, 'r', label='Прогнозирование по году с интервалом в год')

			if year % 5 == 0 and year < 2101:
				x, y = [], []
				for interval in sorted(self.main.big_prediction[year].keys(), key=lambda k: int(k.split('-')[0])):
					x.append(int(interval.split('-')[0]))
					y.append(union_count_genders(self.main.big_prediction[year][interval]))
				ax.plot(x, y, 'b', label='Прогнозирование по 5 годам')

				if year < 2051:
					x, y = [], []
					xml_data = self.main.data_helper.get_prediction(year)[year]
					for interval in sorted(xml_data.keys(), key=lambda k: int(k.split('-')[0])):
						x.append(int(interval.split('-')[0]))
						y.append(union_count_genders(xml_data[interval]))
					ax.plot(x, y, 'y', label='Прогнозирование из xls')

			x, y = [], []
			for index in range(0, 101, 5):
				val = 0
				for i in range(index, index + 5):
					val += union_count_genders(self.main.interval_prediction[year][index])
				x.append(index)
				y.append(val)
			ax.plot(x, y, 'k--', label='Прогнозирование по году суммарное')

			plt.grid()
			plt.legend(loc='best')
			Plot.set_labels(title.format(year), x_label, y_label)
			plt.show()
			# plt.savefig('plots/{}/fig-{}.png'.format(folder, year))
			plt.clf()

	def draw_year(self, year):

		ax = plt.subplot()
		x, y = [], []
		for interval in self.main.interval_prediction[year].keys():
			x.append(int(interval))
			y.append(union_count_genders(self.main.interval_prediction[year][interval]))
		ax.plot(x, y, 'r', label='Прогнозирование по году с интервалом в год')

		x, y = [], []
		for index in range(0, 101, 5):
			val = 0
			for i in range(index, index + 5):
				val += union_count_genders(self.main.interval_prediction[year][index])
			x.append(index)
			y.append(val)
		ax.plot(x, y, 'k--', label='Прогнозирование по году суммарное')
		plt.grid()
		plt.legend(loc='best')
		plt.show()

	def draw_interval_year(self, title):
		predictions = self.main.interval_prediction[2005]
		x, y = list(sorted(predictions.keys())), []
		for xi in x:
			y.append(int(predictions[xi]['male'] + predictions[xi]['female']))
		plt.plot(x, y, '-o')
		plt.show()

	def convert_to_plt(self, array, year):
		result = []
		prev_key, year = '0-4', array[year]
		prev_value = year['0-4']['male'] + year['0-4']['male']
		for interval in self.intervals:
			if interval == '0-4':
				continue
			number = year[interval]['male'] + year[interval]['male']
			keys, values = [prev_key, interval], [prev_value, number]

			result.append({'keys': keys, 'values': values})
			prev_key, prev_value = interval, number

		return result

	@staticmethod
	def set_labels(title, x_label, y_label):
		plt.title(title)
		plt.xlabel(x_label)
		plt.ylabel(y_label)

	@staticmethod
	def draw_prediction(ax, array, color, label):
		add_label = True
		for el in array:
			if add_label:
				ax.plot(el['keys'], el['values'], 'o-', alpha=.8, color=color, label=label)
			else:
				ax.plot(el['keys'], el['values'], 'o-', alpha=.8, color=color)
			add_label = False
