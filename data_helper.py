import logging as log
import xlrd
import xlwt


class DataHelper:

	csv_file = 'russia.csv'
	xls_file = 'age_data.xls'
	w_xls_file = 'out.xls'

	def __init__(self, country, years):
		if years is None:
			years = [2000, 2005]

		self.country = country
		self.years = years

	def get_init_data(self):
		data = {}
		for year in self.years:
			data[year] = {}
		return data

	def read_csv(self):
		log.info('Reading of csv file: {}'.format(self.csv_file))
		f = open(self.csv_file, 'r')
		data_popup = self.get_init_data()
		for line in f:
			if line:
				data = line.split(';')
				data_popup[int(data[0])][data[1]] = {'male': float(data[2]), 'female': float(data[3])}
		f.close()
		return data_popup

	def read_xls(self):
		log.info('Reading of xls file: {}'.format(self.xls_file))
		f = xlrd.open_workbook(self.xls_file)

		male = self.read_xls_sheet(f, 'male')
		female = self.read_xls_sheet(f, 'female')

		data_popup = self.get_init_data()
		for row_num in range(len(self.years)):
			year = int(male[row_num][5])
			age = 0
			for column in range(6, len(male[row_num])):
				el = {'male': male[row_num][column], 'female': female[row_num][column]}
				data_popup[year]['{}-{}'.format(age, age + 4)] = el
				age += 5

		return data_popup

	def get_prediction(self, year):
		log.info('Reading of xls file: {}'.format(self.xls_file))
		f = xlrd.open_workbook(self.xls_file)

		prediction = self.read_xls_sheet(f, 'both;2010-50', [year])
		age = 0
		data_popup = {year: {}}
		for column in range(6, len(prediction[0])):
			el = {'male': prediction[0][column] / 2, 'female': prediction[0][column] / 2}
			data_popup[year]['{}-{}'.format(age, age + 4)] = el
			age += 5
		return data_popup

	def xls_to_csv(self, data):
		log.info('Write data to csv file: {}'.format(self.csv_file))
		f = open(self.csv_file, 'w')
		for year in data:
			for age in data[year]:
				count = data[year][age]
				f.write('{};{};{};{}\n'.format(year, age, count['male'], count['female']))
		f.close()

	def read_xls_sheet(self, file, name, years=None):
		"""
		Get lines on sheet in xls file using country and year filters
		:param file:
		:param name: name of sheet
		:return: list of lines
		"""
		if not years:
			years = self.years
		male = file.sheet_by_name(name)
		male_data = []
		for nrow in range(male.nrows):
			line = []
			row = male.row(nrow)
			for el in row:
				line.append(el.value)

			male_data.append(line)

		# v[2] - Country, v[5] - year
		return list(filter(lambda v: v[2] == self.country and int(v[5]) in years, male_data))

	def write_to_xls(self, titles: list, data: dict, data_by_year: dict, data_by_each_year:dict):
		wb = xlwt.Workbook()
		by_5_years = wb.add_sheet('by_5_years')
		by_year_sheet = wb.add_sheet('by_1_years')
		by_interval_year_sheet = wb.add_sheet('by_1_years_interval_1')
		col = 0
		for title in titles:
			by_5_years.write(0, col, title)
			by_year_sheet.write(0, col, title)
			col += 1
		col = 0

		for interval in ['year'] + list(range(0, 100)) + ['100+']:
			by_interval_year_sheet.write(0, col, interval)
			col += 1

		# write predictions by 5 years
		DataHelper.write_sheet(by_5_years, data)

		# write predictions by 1 years
		DataHelper.write_sheet(by_year_sheet, data_by_year)

		# write predictions by an year and with year intervals
		DataHelper.write_sheet(by_interval_year_sheet, data_by_each_year)

		wb.save(self.w_xls_file)

	@staticmethod
	def write_sheet(sheet, data):
		index = 1
		for year in sorted(data.keys()):
			sheet.write(index, 0, str(year))
			col = 1
			for number in data[year]:
				sheet.write(index, col, str(number))
				col += 1
			index += 1
