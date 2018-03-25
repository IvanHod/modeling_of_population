import matplotlib.pyplot as plt


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

	def draw_compare(self,  title, x_label, y_label):
		ax = plt.subplot()
		array = self.convert_to_plt(self.main.prediction, 2050)
		add_label = True
		for el in array:
			if add_label:
				ax.plot(el['keys'], el['values'], 'o-', alpha=.8, color='g', label='Прогнозирование по году')
			else:
				ax.plot(el['keys'], el['values'], 'o-', alpha=.8, color='g')
			add_label = False

		array = self.convert_to_plt(self.main.big_prediction, 2050)
		add_label = True
		for el in array:
			if add_label:
				ax.plot(el['keys'], el['values'], 'o-', alpha=.8, color='b', label='Прогнозирование по 5 годам')
			else:
				ax.plot(el['keys'], el['values'], 'o-', alpha=.8, color='b')
			add_label = False

		prediction = self.convert_to_plt(self.main.data_helper.get_prediction(2050), 2050)
		add_label = True
		for el in prediction:
			if add_label:
				ax.plot(el['keys'], el['values'], 'o-', alpha=.8, color='r', label='Прогнозирование из xml')
			else:
				ax.plot(el['keys'], el['values'], 'o-', alpha=.8, color='r')
			add_label = False

		plt.legend()
		Plot.set_labels(title, x_label, y_label)
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
