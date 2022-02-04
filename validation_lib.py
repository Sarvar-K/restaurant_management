import sql_queries as q
from connect import get_old_values_from
import psycopg2
import pandas as pd
import re
import datetime as d

# Auxilary-functions------------------------------------------------------------------------

def launch_binary_search(values, value):

    start = 0
    end = len(values) - 1

    while start <= end:
        middle = (start + end)// 2
        midvalue = values[middle]
        if midvalue > value:
            end = middle - 1
        elif midvalue < value:
            start = middle + 1
        else:
            return True 

    return False


# Primary-functions-------------------------------------------------------------------

def request_is_json(request):
	if request.is_json: 
		json = request.get_json()
		if len(json) != 0:
			return json
		return "Request must contain at least one field"
	return "Request must be JSON"

def required():
	def inner(value):
		return None if value != None else "This field is required"
	return inner

def required_new():
	def inner(value):
		if value == "Required field":
			return "Error"
		elif value == "Optional field":
			return None
		return None
	return inner

def check_type(required_type):
	def inner(value):
		if type(value) == int and required_type == float: return None
		if type(value) == required_type: return None
		return "Value {} must be {}".format(value, required_type.__name__)
	return inner

def check_length_less(required_length):
	def inner(value):
		if len(value) < required_length and len(value) != 0: return None
		return "Value '{}' must be less than {} characters".format(value, required_length)
	return inner

def check_length_equal(required_length, field):
	def inner(value):
		if len(value) == 0:
				return "This field cannot be empty"
		if type(required_length) == int:
			if len(value) != required_length:
				return "Value '{}' must be equal to {} characters".format(value, required_length)
		elif required_length is None:
			return "Value '{}' must be equal to the length of value in '{}' field".format(value, field)
		elif type(required_length) == dict or type(required_length) == list:
			if len(value) != len(required_length):
				return "Value '{}' must be equal to the length of value in '{}' field".format(value, field)
		return None
		
	return inner

def check_length_more(required_length):
	def inner(value):
		if len(value) > required_length: return None
		return "Value '{}' must be more than {} characters in length".format(value, required_length)
	return inner

def check_old_values_false(old_values):
	def inner (value):
		if type(value) == str:
			if value.isnumeric(): value = int(value)
			else: value = value.lower()
		if launch_binary_search(sorted(old_values), value) is False: return None
		return "Value {} already exists in the database".format(value)
	return inner

def check_old_values_true(old_values):
	def inner (value):
		if type(value) == str: 
			if value.isnumeric(): value = int(value)
			else: value = value.lower()
		if launch_binary_search(sorted(old_values), value) is True: return None
		return "Value {} does not exist in the database".format(value)
	return inner

def check__phone():
	def inner(value):
		if value[0] != "+":
			return "The phone number must start with the '+' symbol"
		for i in value[1:]:
			if i.isnumeric() == False:
				return "The phone number after '+' symbol must be numeric"
		return None
	return inner

def check__email():
	def inner(value):
		if len(re.findall("@", value)) != 1:
			return "Email must contain exactly one '@' symbol"
		elif re.compile(r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9]+(\.[A-Z|a-z]{2,})+').fullmatch(value):
			return None
		return "Email has incorrect format"

	return inner

def check_integer_key():
	def inner(value):
		if type(value) is str and value.isnumeric(): return None
		return "The key must be integer represented by string, like so: '1'"
	return inner

def check__date(cannot_be_past = False, cannot_be_future = False):
	def inner(value):
		try:
			given_date = d.datetime.strptime(value, "%Y-%m-%d").date()
			today_date = d.date.today()
		except ValueError:
			return "This is the incorrect date string format. It should be YYYY-MM-DD"

		if cannot_be_past == True and given_date < today_date:
			return "Cannot select the past date"

		if cannot_be_future == True and given_date > today_date:
			return "Cannot select the future date"

		return None

	return inner

def check_number(limit):
	def inner(value):
		if value < 0 or value > limit:
			return "Value must be between 0 and {}".format(limit)
		return None
	return inner

# Secondary-functions------------------------------------------------------------------

def compose_validations(validations):
	def validate(value):
		for check in validations:
			error = check(value)
			if error != None: return error

		return None
	return validate

def validate_if(boole):
	def inner(validate):
		def noop(*args):pass

		if boole == True:
			return validate
		
		return noop
			
	return inner

def validate_list(validations):
	def inner(lst):
		checks = compose_validations(validations)
		for i in lst:
			error = checks(i)
			if error != None: return error
		return None
	return inner


def validate_dictionary(key_validations, value_validations):
	def inner(dictionary):
		key_checks = compose_validations(key_validations)
		value_checks = compose_validations(value_validations)
		for i in dictionary:
			error = key_checks(i)
			if error != None: return error + " (in key '{}')".format(i)
			error = value_checks(dictionary[i])
			if error != None: return error + " (in value for key '{}')".format(i)
		return None
	return inner


def check__dependencies(table, column):
	potential_conflicts = sorted(get_old_values_from(table, column))
	def inner(value):
		if launch_binary_search(potential_conflicts, value):
			return "This value is referenced in column {} of {} table".format(column, table)
		return None
	return inner
