from scipy import interpolate


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


# надо сделать разделение по полу
def split_interval(interval: dict) -> dict:
	result = {}
	for number in interval:
		rn = list(map(lambda x: int(x), number.split('-')))
		male, female = interval[number]['male'] / 5, interval[number]['female']
		for age in range(rn[0], rn[1] + 1):
			result[age] = {'male': male, 'female': female}
	return result
