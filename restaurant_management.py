from flask import Flask, request, jsonify
import psycopg2
from config import config
import pandas as pd
import sql_queries as q
from connect import parse_post_request, execute_request, get_old_values_from
from validation_lib import *
import datetime as d

app = Flask(__name__)


def categorize(result, categories_column, rows_to_categorize):
	# For example: (..., [Fruits, Vegetables, Dairy] as "category", [Apples, Parmesan, Carrots, Oranges, Potatoes] as "ingredients")
	# category, [category_id, ingredient, ingredient_id]

	n = 0

	categories = result[categories_column]
	# There must be at least 2 distinct categories
	d = result[rows_to_categorize]
	columns = [i for i in result]
	columns.remove(categories_column)
	columns.remove(rows_to_categorize)

	while n < len(categories):

	    if categories[n-1] != categories[n]:
	        result[categories[n]] = {}

	    result[categories[n]][d[n]] = {}

	    for i in columns:
	    	result[categories[n]][d[n]][i] = result[i][n]

	    n += 1

	del result[categories_column]
	del result[rows_to_categorize]

	for i in columns:
		del result[i]


	return result

def isolate_to_dictionary(result, first_index_columns, primary_category_name, subcategories_column, all_index_columns):

	# ["dish", "is_active", "price"], "ingredients", "pre_ingredients", ["amount_per_serving", "is_allergen", "measure"]
    # ["dish", "number_of_servings"], "ingredients", "ingredient", ["number_of_servings"]


    # select first entry as max or min in category or as category name

    result[primary_category_name] = {}

    n = 0

    subcategories = result[subcategories_column]

    if len(all_index_columns) == 1:
    	values = result[all_index_columns[0]]
    	for i in first_index_columns:
        	result[i] = result[i][0]
    	while n < len(subcategories):
    		result[primary_category_name][subcategories[n]] = int(values[n])
    		n += 1

    else:
    	for i in first_index_columns:
    		result[i] = result[i][0]
    	while n < len(subcategories):
    		result[primary_category_name][subcategories[n]] = {}
    		for i in all_index_columns:
    			result[primary_category_name][subcategories[n]][i] = result[i][n]
    		n += 1
    	for i in all_index_columns:
    		del result[i]


        
    del result[subcategories_column]

    return result

def pair(result):
	dictionary = {}
	fields = []
	n = 0
	for i in result:
		fields.append(i)

	while n < len(result[fields[0]]):
		dictionary[result[fields[0]][n]] = result[fields[1]][n]
		n += 1

	return dictionary

def deep_pair(result, main_column_name):

	other_columns = []

	for i in result:
		other_columns.append(i)

	other_columns.remove(main_column_name)

	main_column = result[main_column_name]

	n = 0

	while n < len(main_column):

		result[main_column[n]] = {}

		for i in other_columns:

			result[main_column[n]][i] = result[i][n]

		n += 1

	#return result
	del result[main_column_name]

	for i in other_columns:
		del result[i]

	return result

def search_for_errors(errors):
	error = None
	for i in errors:
		if errors[i] != None:
			error = errors
			break
	return error


@app.route("/dish_categories", methods = ["GET"])
def get_dish_categories():

	result = execute_request(q.dish_categories, "list", 200, after_execution = pair)

	return jsonify(result[0]), result[1]

@app.route("/dish_categories", methods = ["POST"])
def add_dish_category():

	json = request_is_json(request)

	if type(json) is not dict: return jsonify({"error": json}), 400

	check_name = compose_validations([required(), check_type(str), check_length_less(50), check_old_values_false(get_old_values_from("dish_categories", "name"))])

	errors = {
		"name": check_name(json.get("name", None))
	}

	if search_for_errors(errors) is not None: return jsonify({"error": errors}), 400

	result = execute_request(q.add_rows, "index", 201, query_params = ["dish_categories", json])

	return jsonify(result[0]), result[1]

@app.route("/dish_categories/<int:id>", methods = ["PUT"])
def edit_dish_category(id):

	json = request_is_json(request)

	if type(json) is not dict: return jsonify({"error": json}), 400

	check_id = compose_validations([check_old_values_true(get_old_values_from("dish_categories", "id"))])
	check_name = compose_validations([required(), check_type(str), check_length_less(50), check_old_values_false(get_old_values_from("dish_categories", "name"))])

	errors = {
		"id": check_id(id),
		"name": check_name(json.get("name", None))
	}

	if search_for_errors(errors) == None: return jsonify({"error": errors}), 400

	result = execute_request(q.update_row, "index", 200, query_params = ["dish_categories", "id", json, id])

	return jsonify(result[0]), result[1]

@app.route("/dish_categories/<int:id>", methods = ["DELETE"])
def delete_dish_category(id):

	check_id = compose_validations([check_old_values_true(get_old_values_from("dish_categories", "id"))])

	errors = {
		"id": check_id(id)
	}

	if search_for_errors(errors) == None:

		result = execute_request(q.delete_value, "index", 200, query_params = ["dish_categories", "id", id])

		return jsonify(result[0]), result[1]

	return jsonify({"error": errors}), 400

@app.route("/ingredient_categories", methods = ["GET"])
def get_ingredient_categories():

	result = execute_request(q.ingredient_categories, "list", 200, after_execution = pair)

	return jsonify(result[0]), result[1]

@app.route("/ingredient_categories", methods = ["POST"])
def add_ingredient_category():

	json = request_is_json(request)

	if type(json) == dict:

		check_name = compose_validations([required(), check_type(str), check_length_less(70), check_old_values_false(get_old_values_from("ingredient_categories", "name"))])

		errors = {
			"name": check_name(json.get("name", None))
		}

		if search_for_errors(errors) == None:

			result = execute_request(q.add_rows, "index", 201, query_params = ["ingredient_categories", json])

			return jsonify(result[0]), result[1]

		return jsonify({"error": errors}), 400

	return jsonify({"error": json}), 400

@app.route("/ingredient_categories/<int:id>", methods = ["PUT"])
def edit_ingredient_category(id):

	json = request_is_json(request)

	if type(json) == dict:

		check_id = compose_validations([check_old_values_true(get_old_values_from("ingredient_categories", "id"))])
		check_name = compose_validations([required(), check_type(str), check_length_less(70), check_old_values_false(get_old_values_from("ingredient_categories", "name"))])

		errors = {
			"id": check_id(id),
			"name": check_name(json.get("name", None))
		}

		if search_for_errors(errors) == None:

			result = execute_request(q.update_row, "index", 200, query_params = ["ingredient_categories", "id", json, id])

			return jsonify(result[0]), result[1]

		return jsonify({"error": errors}), 400

	return jsonify({"error": json}), 400

@app.route("/ingredient_categories/<int:id>", methods = ["DELETE"])
def delete_ingredient_category(id):

	check_id = compose_validations([check_old_values_true(get_old_values_from("ingredient_categories", "id"))])

	errors = {
		"id": check_id(id)
	}

	if search_for_errors(errors) == None:

		result = execute_request(q.delete_value, "index", 200, query_params = ["ingredient_categories", "id", id])

		return jsonify(result[0]), result[1]

	return jsonify({"error": errors}), 400

@app.route("/ingredients", methods = ["GET"])
def get_ingredients():

	result = execute_request(q.all_ingredients, "list", 200, after_execution = categorize, function_parameters = ["category", "ingredient"])

	return jsonify(result[0]), result[1]

@app.route("/ingredients", methods = ["POST"])
def add_ingredient():

	json = request_is_json(request)

	if type(json) == dict:

		name = json.get("name", None)
		is_allergen = json.get("is_allergen", None)
		measure_id = json.get("measure_id", None)
		ingredient_categories_id = json.get("ingredient_categories_id", None)


		check_name = compose_validations([required(), check_type(str), check_length_less(50), check_old_values_false(get_old_values_from("ingredients", "name"))])
		check_is_allergen = compose_validations([check_type(bool)])
		check_measure_id = compose_validations([required(), check_type(int), check_old_values_true(get_old_values_from("measures", "id"))])
		check_ingredient_categories_id = compose_validations([required(), check_type(int), check_old_values_true(get_old_values_from("ingredient_categories", "id"))])

		errors = {
			"name": check_name(name),
			"is_allergen": validate_if(is_allergen is not None)(check_is_allergen)(is_allergen),
			"measure_id": check_measure_id(measure_id),
			"ingredient_categories_id": check_ingredient_categories_id(ingredient_categories_id)
		}

		if search_for_errors(errors) == None:

			result = execute_request(q.add_rows, "index", 201, query_params = ["ingredients", json])

			return jsonify(result[0]), result[1]

		return jsonify({"error": errors}), 400

	return jsonify({"error": json}), 400

@app.route("/ingredients/<int:id>", methods = ["PATCH"])
def edit_ingredient_description(id):

	json = request_is_json(request)

	if type(json) is not dict: return jsonify({"error": json}), 400

	name = json.get("name", None)
	is_allergen = json.get("is_allergen", None)
	measure_id = json.get("measure_id", None)
	ingredient_categories_id = json.get("ingredient_categories_id", None)

	check_ingredient_id = compose_validations([check_old_values_true(get_old_values_from("ingredients", "id"))])
	check_name = compose_validations([check_type(str), check_length_less(50), check_old_values_false(get_old_values_from("ingredients", "name"))])
	check_is_allergen = compose_validations([check_type(bool)])
	check_measure_id = compose_validations([check_type(int), check_old_values_true(get_old_values_from("measures", "id"))])
	check_ingredient_categories_id = compose_validations([check_type(int), check_old_values_true(get_old_values_from("ingredient_categories", "id"))])

	errors = {
		"id": check_ingredient_id(id),
		"name": validate_if(name is not None)(check_name)(name),
		"is_allergen": validate_if(is_allergen is not None)(check_is_allergen)(is_allergen),
		"measure_id": validate_if(measure_id is not None)(check_measure_id)(measure_id),
		"ingredient_categories_id": validate_if(ingredient_categories_id is not None)(check_ingredient_categories_id)(ingredient_categories_id)
	}

	if search_for_errors(errors) is not None: return jsonify({"error": errors}), 400

	result = execute_request(q.update_row, "index", 200, query_params = ["ingredients", "id", json, id])

	return jsonify(result[0]), result[1]	

@app.route("/ingredients/<int:id>", methods = ["DELETE"])
def delete_ingredient(id):

	check_id = compose_validations([check_old_values_true(get_old_values_from("ingredients", "id")), 
		check__dependencies("ingredients_in_dishes", "ingredient_id"), check__dependencies("shipments", "ingredient_id")])

	errors = {
		"id": check_id(id)
	}

	if search_for_errors(errors) is not None: return jsonify({"error": errors}), 400

	result = execute_request(q.delete_value, "index", 200, query_params = ["ingredients", "id", id])

	return jsonify(result[0]), result[1]	

@app.route("/dishes", methods = ["GET"])
def get_dishes():

	result = execute_request(q.dishes, "list", 200, after_execution = categorize, function_parameters = ["category", "dishes"])

	return jsonify(result[0]), result[1]

@app.route("/dishes", methods = ["POST"])
def add_dish():

	json = request_is_json(request)

	if type(json) is not dict: return jsonify({"error": json}), 400

	name = json.get("name", None)
	price = json.get("price", None)
	category_id = json.get("category_id", None)
	is_active = json.get("is_active", None)

	check_name = compose_validations([required(), check_type(str), check_length_less(70), check_old_values_false(get_old_values_from("dishes", "name"))])
	check_price = compose_validations([required(), check_type(float), check_number(99999999999)])
	check_category_id = compose_validations([required(), check_type(int), check_old_values_true(get_old_values_from("dish_categories", "id"))])
	check_is_active = compose_validations([check_type(bool)])

	errors = {
		"name": check_name(name),
		"price": check_price(price),
		"category_id": check_category_id(category_id),
		"is_active": validate_if(is_active is not None)(check_is_active)(is_active)
	}

	if search_for_errors(errors) is not None: return jsonify({"error": errors}), 400

	price = round(price, 2)

	result = execute_request(q.add_rows, "index", 201, query_params = ["dishes", json])

	return jsonify(result[0]), result[1]	

@app.route("/dishes/<int:id>", methods = ["DELETE"])
def delete_dish(id):

	check_id = compose_validations([check_old_values_true(get_old_values_from("dishes", "id"))])

	errors = {
		"id": check_id(id)
	}

	if search_for_errors(errors) == None:

		result = execute_request(q.delete_value, "index", 200, query_params = ["dishes", "id", id])

		return jsonify(result[0]), result[1]

	return jsonify({"error": errors}), 400

@app.route("/dishes/<int:id>", methods = ["GET"])
def get_dish_ingredients(id):

	error = compose_validations([check_old_values_true(get_old_values_from("dishes", "id"))])(id)

	if error is not None: return jsonify({"error": error}, 400)

	result = execute_request(q.dish_ingredients, "list", 200, query_params = [id], after_execution = isolate_to_dictionary, 
		function_parameters = [["dish", "is_active", "price"], "ingredients", "pre_ingredients", ["amount_per_serving", "is_allergen", "measure"]])

	return jsonify(result[0]), result[1]	

@app.route("/dishes/<int:id>/populate", methods = ["POST"])
def add_initial_ingredients_in_dish(id):

	json = request_is_json(request)

	if type(json) is not dict: return jsonify({"error": json}), 400

	check_id = compose_validations([check_old_values_true(get_old_values_from("dishes", "id")), check_old_values_false(get_old_values_from("ingredients_in_dishes", "dish_id"))])
	check_ingredient_amounts = compose_validations([required(), check_type(dict), check_length_more(0), 
		validate_dictionary([check_integer_key(), check_old_values_true(get_old_values_from("ingredients", "id"))], 
		[check_type(int), check_number(9223372036854775807)])])

	errors = {
		"dish_id": check_id(id),
		"ingredients_amounts": check_ingredient_amounts(json)
	}

	if search_for_errors(errors) is not None: return jsonify({"error": errors}), 400

	result = execute_request(q.add_ingredients_in_dish, "index", 201, query_params = [json, id])

	return jsonify(result[0]), result[1]	

@app.route("/dishes/<int:id>/add", methods = ["POST"])
def add_new_ingredients_in_dish(id):

	json = request_is_json(request)

	if type(json) is not dict: return jsonify({"error": json}), 400

	check_ingredient_amounts = compose_validations([required(), check_type(dict), check_length_more(0), 
		validate_dictionary([check_integer_key(), check_old_values_true(get_old_values_from("ingredients", "id")), 
			check_old_values_false(get_old_values_from("ingredients_in_dishes", "ingredient_id", WHERE_left = "dish_id", WHERE_right = id))], [check_type(int), check_number(9223372036854775807)])])

	dish_id_error = check_old_values_true(get_old_values_from("ingredients_in_dishes", "dish_id"))(id)

	errors = {
		"dish_id": dish_id_error,
		"ingredients_amounts": validate_if(dish_id_error is None)(check_ingredient_amounts)(json)
	}

	if search_for_errors(errors) is not None: return jsonify({"error": errors}), 400

	result = execute_request(q.add_ingredients_in_dish, "index", 201, query_params = [json, id])

	return jsonify(result[0]), result[1]	

@app.route("/dishes/<int:id>/ingredients", methods = ["DELETE"])
def delete_ingredients_in_dish(id):

	json = request_is_json(request)

	if type(json) == dict:

		check_ingredients = compose_validations([required(), check_type(list), check_length_more(0), 
			validate_list([check_type(int), check_old_values_true(get_old_values_from("ingredients_in_dishes", "ingredient_id", WHERE_left = "dish_id", WHERE_right = id))])])

		dish_id_error = check_old_values_true(get_old_values_from("ingredients_in_dishes", "dish_id"))(id)
		ingredient_ids = json.get("ingredients", None)

		errors = {
			"dish_id": dish_id_error,
			"ingredients": validate_if(dish_id_error is None)(check_ingredients)(ingredient_ids)
		}

		if search_for_errors(errors) == None:

			result = execute_request(q.delete_value("ingredients_in_dishes", "dish_id", id, ids = ingredient_ids, secondary_key = "ingredient_id"), "index", 201)

			return jsonify(result[0]), result[1]

		return jsonify({"error": errors}), 400

	return jsonify({"error": json}), 400

@app.route("/dishes/<int:id>", methods = ["PATCH"])
def edit_dish_description(id):

	json = request_is_json(request)

	if type(json) is not dict: return jsonify({"error": json}), 400

	name = json.get("name", None)
	price = json.get("price", None)
	category_id = json.get("category_id", None)
	is_active = json.get("is_active", None)
	ingredients_amounts = json.get("ingredients_amounts", None)

	check_id = compose_validations([check_old_values_true(get_old_values_from("ingredients_in_dishes", "dish_id"))])
	check_name = compose_validations([check_type(str), check_length_less(70), check_old_values_false(get_old_values_from("dishes", "name"))])
	check_price = compose_validations([check_type(float), check_number(99999999999)])
	check_category_id = compose_validations([check_type(int), check_old_values_true(get_old_values_from("dish_categories", "id"))])
	check_is_active = compose_validations([check_type(bool)])
	check_ingredients_amounts = compose_validations([check_type(dict), check_length_more(0), 
		validate_dictionary([check_integer_key(), check_old_values_true(get_old_values_from("ingredients_in_dishes", "ingredient_id", WHERE_left = "dish_id", WHERE_right = id))], 
			[check_type(int), check_number(9223372036854775807)])])

	errors = {
		"id": check_id(id),
		"name": validate_if(name is not None)(check_name)(name),
		"price": validate_if(price is not None)(check_price)(price),
		"category_id": validate_if(category_id is not None)(check_category_id)(category_id),
		"is_active": validate_if(is_active is not None)(check_is_active)(is_active),
		"ingredients_amounts": validate_if(ingredients_amounts is not None)(check_ingredients_amounts)(ingredients_amounts)
	}

	if search_for_errors(errors) is not None: return jsonify({"error": errors}), 400

	if price is not None: price = round(price, 2)		

	if ingredients_amounts is None: result = execute_request(q.update_row, "index", 200, query_params = ["dishes", "id", json, id])[0]

	else:

		ingredients_result = execute_request(q.update_rows, "list", 200, query_params = ["ingredients_in_dishes", "amount_per_serving", 
			"dish_id", "ingredient_id", ingredients_amounts, id])

		del json["ingredients_amounts"]

		dishes_result = execute_request(q.update_row, "index", 200, query_params = ["dishes", "id", json, id])

		result = {**dishes_result[0][0], **ingredients_result[0]}		

	return jsonify(result), 200	

@app.route("/dishes/<int:id>/check", methods = ["GET"])
def get_dish_check(id):

	error = compose_validations([check_old_values_true(get_old_values_from("dishes", "id"))])(id)

	if error is not None: return jsonify({"error": error}, 400)

	result = execute_request(q.dish_check, "list", 200, query_params = [id], after_execution = isolate_to_dictionary,
		function_parameters = [["dish", "number_of_servings"], "ingredients", "ingredient", ["number_of_servings"]])

	return jsonify(result[0]), result[1]

@app.route("/stock", methods = ["GET"])
def get_stock():

	result = execute_request(q.stock, "list", 200, after_execution = categorize, function_parameters = ["category", "ingredient"])

	return jsonify(result[0]), result[1]

@app.route("/stock/<int:id>", methods = ["GET"])
def get_ingredient_shipments(id):

	error = compose_validations([check_old_values_true(get_old_values_from("ingredients", "id"))])(id)

	if error is not None: return jsonify({"error": error}, 400)

	if check_old_values_true(get_old_values_from(None, "ingredient_id", custom_query = q.current_ingredient_amounts))(id) is not None:

		result = execute_request(q.get_ingredient_in_stock, "index", 200, query_params = [0, id])

	else:

		result = execute_request(q.get_ingredient_in_stock, "list", 200, query_params = [1, id], after_execution = isolate_to_dictionary, 
			function_parameters = [["ingredient_id", "ingredient", "total_amount", "measure"], "shipments", "shipment_id", ["current_amount", "due_date"]])

		json = result[0]

		shipments = json.get("shipments", None)

		if shipments is not None:

			for i in shipments:

				if shipments[i]["due_date"] is None: shipments[i]["should_remain_active"] = True

				if d.date.today() > shipments[i]["due_date"] or shipments[i]["current_amount"] != 0: shipments[i]["should_remain_active"] = False
					
				else:

					shipments[i]["should_remain_active"] = True						

	return jsonify(result[0]), result[1]	

@app.route("/stock/<int:id>", methods = ["POST"]) 
def add_ingredient_shipment(id):

	json = request_is_json(request)

	if type(json) is not dict: return jsonify({"error": json}), 400

	supplier_id = json.get("supplier_id", None)	
	date_supplied = json.get("date_supplied", None)
	due_date = json.get("due_date", None)
	shipment_price = json.get("shipment_price", None)
	shipment_size = json.get("shipment_size", None)
	is_active = json.get("is_active", None)

	check_supplier = compose_validations([required(), check_type(int), check_old_values_true(get_old_values_from("suppliers", "id"))])
	check_date_supplied = compose_validations([check_type(str), check__date(cannot_be_future = True)])
	check_due_date = compose_validations([check_type(str), check__date(cannot_be_past = True)])
	check_price = compose_validations([check_type(float), check_number(99999999999)])
	check_size = compose_validations([required(), check_type(int), check_number(9223372036854775807)])
	check_active = compose_validations([check_type(bool)])

	id_error = check_old_values_true(get_old_values_from("ingredients", "id"))(id)

	errors = {
		"id": id_error,
		"supplier_id": check_supplier(supplier_id),
		"date_supplied": validate_if(date_supplied is not None)(check_date_supplied)(date_supplied),
		"due_date": validate_if(due_date is not None)(check_due_date)(due_date),
		"shipment_price": validate_if(shipment_price is not None)(check_price)(shipment_price),
		"shipment_size": check_size(shipment_size),
		"is_active": validate_if(is_active is not None)(check_active)(is_active)
	}

	if search_for_errors(errors) is not None: return jsonify({"error": errors}), 400

	if shipment_price is not None:
		shipment_price = round(shipment_price, 2)

	shipments_json = json.copy()

	shipments_json["ingredient_id"] = id
	ingredients_json = {}

	if is_active is not None:
		del shipments_json["is_active"]
		ingredients_json["is_active"] = is_active

	shipments_result = execute_request(q.add_rows, "index", 201, query_params = ["shipments", shipments_json])

	shipment_id = shipments_result[0][0]["id"]

	ingredients_json["shipment_id"] = shipment_id
	ingredients_json["current_amount"] = shipment_size

	ingredients_result = execute_request(q.add_rows, "index", 201, query_params = ["ingredients_in_stock", ingredients_json])

	result = {**shipments_result[0][0], **ingredients_result[0][0]}

	return jsonify(result), ingredients_result[1]	

@app.route("/stock/<int:ingredient_id>/<int:shipment_id>", methods = ["GET"]) 
def get_shipment_details(ingredient_id, shipment_id):

	ingredient_error = check_old_values_true(get_old_values_from("ingredients", "id"))(ingredient_id)
	shipment_error = check_old_values_true(get_old_values_from("shipments", "id", WHERE_left = "ingredient_id", WHERE_right = ingredient_id))(shipment_id)

	errors = {
		"ingredient_id": ingredient_error,
		"shipment_id": shipment_error
	}

	if search_for_errors(errors) is not None: return jsonify({"error": errors}, 400)

	result = execute_request(q.get_shipment_details, "index", 200, query_params = [ingredient_id, shipment_id])[0]	

	return jsonify(result[0]), 200	

@app.route("/measures", methods = ["GET"])
def get_measures():

	result = execute_request(q.measures, "list", 200, after_execution = pair)

	return jsonify(result[0]), result[1]

@app.route("/suppliers", methods = ["GET"])
def get_suppliers():

	result = execute_request(q.suppliers, "list", 200, after_execution = deep_pair, function_parameters = ["name"])

	return jsonify(result[0]), result[1]

@app.route("/supplier_types", methods = ["GET"])
def get_supplier_types():

	result = execute_request(q.supplier_types, "list", 200, after_execution = pair)

	return jsonify(result[0]), result[1]

@app.route("/supplier_types", methods = ["POST"])
def add_supplier_type():

	json = request_is_json(request)

	if type(json) is str: return jsonify({"error": json}), 400

	check_name = compose_validations([required(), check_type(str), check_length_less(50), check_old_values_false(get_old_values_from("supplier_types", "name"))])

	errors = {
		"name": check_name(json.get("name", None))
	}

	if search_for_errors(errors) is not None: return jsonify({"error": errors}), 400

	result = execute_request(q.add_rows, "index", 201, query_params = ["supplier_types", json])

	return jsonify(result[0]), result[1]

@app.route("/suppliers", methods = ["POST"])
def add_supplier():

	json = request_is_json(request)

	if type(json) is str: return jsonify({"error": json}), 400

	check_name = compose_validations([required(), check_type(str), check_length_less(70), check_old_values_false(get_old_values_from("suppliers", "name"))])
	check_type_id = compose_validations([required(), check_type(int), check_old_values_true(get_old_values_from("supplier_types", "id"))])
	check_phone = compose_validations([check_type(str), check_length_less(15), check_length_more(10), check__phone()])
	check_email = compose_validations([check_type(str), check_length_less(100), check__email()])

	errors = {
		"name": check_name(json.get("name", None)),
		"supplier_type_id": check_type_id(json.get("supplier_type_id", None)),
		"telephone": validate_if(json.get("telephone", None) != None)(check_phone)(json.get("telephone", None)),
		"email": validate_if(json.get("email", None) != None)(check_email)(json.get("email", None))
	}

	if search_for_errors(errors) is not None: return jsonify({"error": errors}), 400

	result = execute_request(q.add_rows, "index", 201, query_params = ["suppliers", json])

	return jsonify(result[0]), result[1]

	

	



if __name__ == '__main__':

	connection = None



