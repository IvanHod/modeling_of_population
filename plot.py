import matplotlib.pyplot as plt
from tools import *


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
		for year in range(2010, 2051, 20):
			ax = plt.subplot()
			x, y = [], []
			for interval in sorted(self.main.prediction[year].keys(), key=lambda k: int(k.split('-')[0])):
				x.append(int(interval.split('-')[0]))
				y.append(union_count_genders(self.main.prediction[year][interval]))
			ax.plot(x, y, 'g', label='Прогнозирование по году')

			x, y = [], []
			for interval in self.main.interval_prediction[year].keys():
				x.append(int(interval))
				y.append(union_count_genders(self.main.interval_prediction[year][interval]))
			ax.plot(x, y, 'r', label='Прогнозирование по году')

			if year % 5 == 0:
				x, y = [], []
				for interval in sorted(self.main.big_prediction[year].keys(), key=lambda k: int(k.split('-')[0])):
					x.append(int(interval.split('-')[0]))
					y.append(union_count_genders(self.main.big_prediction[year][interval]))
				ax.plot(x, y, 'b', label='Прогнозирование по 5 годам')

				# prediction = self.convert_to_plt(self.main.data_helper.get_prediction(year), year)
				# Plot.draw_prediction(ax, prediction, 'r', 'Прогнозирование из xml')

			plt.grid()
			plt.legend()
			Plot.set_labels(title.format(year), x_label, y_label)
			plt.savefig('plots/{}/fig-{}.png'.format(folder, year))
			plt.clf()
		# plt.show()

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
