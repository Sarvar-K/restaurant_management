dishes = '''select
			  ps.servings,
			  d.id,
			  d.name as dishes,
			  d.price,
			  d.is_active,
			  dc.name as category
			from		
			  (select a.id, min(a.number_of_servings) as servings from (				  
			    select
			      d.id,
			      iid.ingredient_id,
			      floor(sum(coalesce(current_amount,0))/iid.amount_per_serving) as number_of_servings
			    from dishes as d
			    inner join ingredients_in_dishes as iid
			    on iid.dish_id = d.id
			    left join shipments as sh
			    on sh.ingredient_id = iid.ingredient_id
			    left join ingredients_in_stock as iis
			    on iis.shipment_id = sh.id and iis.is_active is true
			    group by d.id, iid.ingredient_id, iid.amount_per_serving			    
			  ) as a
			  group by a.id) as ps			  
			right join dishes as d
			on d.id = ps.id
			inner join dish_categories as dc
			on dc.id = d.category_id
			order by category'''


def dish_ingredients(id):
	ingredients = '''select
						d.name as dish,
						d.price,
						d.is_active,
						i.name as pre_ingredients,
						i.is_allergen,
						iid.amount_per_serving,
						m.name as measure
						from dishes as d
						inner join ingredients_in_dishes as iid
						on iid.dish_id = d.id
						inner join ingredients as i
						on iid.ingredient_id = i.id
						inner join measures as m
						on i.measure_id = m.id
						where d.id = {}'''.format(id)
	return ingredients

def dish_check(id):
	available_portions = '''select
					d2.name as dish,
					i.name as ingredient,
					a.number_of_servings
				from
					(select
						d.id as dish_id,
					    iid.ingredient_id,
					    floor(sum(coalesce(current_amount,0))/iid.amount_per_serving) as number_of_servings
					from dishes as d
					inner join ingredients_in_dishes as iid
					on iid.dish_id = d.id
					left join shipments as sh
					on sh.ingredient_id = iid.ingredient_id
					left join ingredients_in_stock as iis
					on iis.shipment_id = sh.id and iis.is_active is true
					group by d.id, iid.ingredient_id, iid.amount_per_serving) as a
				inner join dishes as d2
				on d2.id = a.dish_id
				inner join ingredients as i
				on a.ingredient_id = i.id
				where d2.id = {}
				order by a.dish_id, a.number_of_servings'''.format(id)
	return available_portions

stock = '''select
			ic.name as category,
			i.id,
			i.name as ingredient,
			coalesce(a.amount, 0) as amount,
			m.name as measure
		from ingredient_categories as ic
		inner join ingredients as i
		on i.ingredient_categories_id = ic.id
		inner join measures as m
		on i.measure_id = m.id
		left join
			(select
				sh.ingredient_id,
				sum(iis.current_amount) as amount
			from shipments as sh
			inner join ingredients_in_stock as iis
			on iis.shipment_id = sh.id and iis.is_active = true
			group by ingredient_id) as a
		on a.ingredient_id = i.id
		order by category, ingredient'''

dish_categories = '''select id, name from dish_categories'''

ingredient_categories = '''select id, name from ingredient_categories'''

measures = '''select id, name from measures'''

all_ingredients = '''select
					i.id as ingredient_id,
					i.name as ingredient,
					ic.id as category_id,
					ic.name as category
				from ingredients as i
				inner join ingredient_categories as ic
				on i.ingredient_categories_id = ic.id
				order by category'''

def add_rows(table, json):

	keys = []
	vals = []

	for i in json:
		keys.append(i)
		vals.append(json[i])

	fields = ", "
	values = ", "

	#vals = ["'{}'".format(i) if type(i) is str else "null" if type(i) is None else str(i) for i in vals]

	vals2 = []

	for i in vals:
		if type(i) is str:
			vals2.append("'{}'".format(i))
		elif i is None:
			vals2.append("null")
		else:
			vals2.append(str(i))

	vals = vals2

	query = '''insert into {} ({})
					values ({})
					returning *'''.format(table, fields.join(keys), values.join(vals))
	return query

def get_column(table):
	def query(column, WHERE_left, WHERE_right):
		if WHERE_left is not None and WHERE_right is not None:
			return '''select {} from {} where {} = {}'''.format(column, table, WHERE_left, WHERE_right)
		return '''select {} from {}'''.format(column, table)
	return query

suppliers = '''select
				s.id,
				s."name",
				s.telephone,
				s.email,
				s.supplier_type_id as type_id,
				st.name as "type"
			from suppliers as s
			inner join supplier_types as st
			on s.supplier_type_id = st.id'''

supplier_types = '''select * from supplier_types'''

def update_row(table, primary_key, json, id):

	keys = []
	vals = []

	for i in json:
		keys.append(i)
		vals.append(json[i])

	string = ""

	n = 0

	while n < len(keys):

		if type(vals[n]) == str:
			string += "{} = '{}', ".format(keys[n], vals[n])
		else:
			string += "{} = {}, ".format(keys[n], vals[n])

		n += 1

	string = string[:-2]

	query = ''' update {}
				set {}
				where {} = {}
				returning *'''.format(table, string, primary_key, id)

	return query

def update_rows(table, column_to_edit, primary_key, secondary_key, json, id): 

	keys = []
	vals = []

	for i in json:
		keys.append(i)
		vals.append(json[i])

	string = ""

	n = 0

	while n < len(keys):

		if type(vals[n]) is None:
			vals[n] = "null"

		string += "({}, {}), ".format(keys[n], vals[n])

		n += 1

	string = string[:-2]

	query =  '''update {} 
				set
				    {} = c.column_a
				from (values {} 
				) as c(column_b, column_a) 
				where c.column_b = {}.{} and {} = {} 
				returning ingredient_id, {};'''.format(table, column_to_edit, string, table, secondary_key, primary_key, id, column_to_edit)

	return query

def delete_value(table, primary_key, id, operator = " = ", ids = None, secondary_key = None):

	if ids is None and secondary_key is None:
		query_filter = primary_key + operator + str(id)
	else:
		values = ", "
		ids = [str(i) for i in ids]
		vals = values.join(ids)
		id_list = "({})".format(vals)
		query_filter = primary_key + operator + str(id) + " and " + secondary_key + " in " + id_list

	rows_to_delete = '''delete from {}
						where {}
						returning *'''.format(table, query_filter)

	return rows_to_delete

def get_ingredients_in_dish(id):

	query = '''select ingredient_id
				from ingredients_in_dishes
				where dish_id = {}
				order by ingredient_id'''.format(id)

	return query

def add_ingredients_in_dish(json, id):

	ingredients = []
	amounts = []

	for i in json:
		ingredients.append(int(i))
		amounts.append(json[i])

	fields = ", "

	n = 0
	string = '''values '''

	while n < len(ingredients):
		string += '''({}, {}, {}),'''.format(ingredients[n], id, amounts[n])
		n += 1

	string = string[:-1]

	new_dish_ingredients =   '''insert into ingredients_in_dishes (ingredient_id, dish_id, amount_per_serving)
								{}
								returning *'''.format(string)
	return new_dish_ingredients

def update_ingredient_in_dish(json, id):

	keys = [i for i in json]
	keys.append("dish_id")

	ingredients = json["ingredient_id"]
	amounts = json["amount_per_serving"]

	fields = ", "

	n = 0
	string = '''values '''

	while n < len(ingredients):
		string += '''({}, {}, {}),'''.format(ingredients[n], amounts[n], id)
		n += 1

	string = string[:-1]

	new_dish_ingredients = '''insert into ingredients_in_dishes ({})
					{}
					returning *'''.format(fields.join(keys), string)
	return new_dish_ingredients

def get_ingredient_in_stock(amount, id):

	if amount > 0:

		query = '''select
					i.id as ingredient_id,
					i.name as ingredient,
					coalesce(a.amount, 0) as total_amount,
					iis2.shipment_id,
					iis2.current_amount,
					m.name as measure,
					s.due_date
				from ingredient_categories as ic
				inner join ingredients as i
				on i.ingredient_categories_id = ic.id
				inner join measures as m
				on i.measure_id = m.id
				left join
					(select
						sh.ingredient_id,
						sum(iis.current_amount) as amount
					from shipments as sh
					inner join ingredients_in_stock as iis
					on iis.shipment_id = sh.id and iis.is_active = true
					group by ingredient_id) as a
				on a.ingredient_id = i.id
				full outer join shipments as s
				using (ingredient_id)
				inner join ingredients_in_stock as iis2
				on s.id = iis2.shipment_id
				where i.id = {} and iis2.is_active = true'''.format(id)

	else:

		query = '''select
					i.id as ingredient_id,
					i.name as ingredient,
					0 as total_amount,
					m.name as measure
				from ingredients as i
				inner join measures as m
				on i.measure_id = m.id
				where i.id = {}'''.format(id)

	return query

current_ingredient_amounts = '''select
									sh.ingredient_id
								from shipments as sh
								inner join ingredients_in_stock as iis
								on iis.shipment_id = sh.id and iis.is_active = true'''

def get_shipment_details(ingredient_id, shipment_id):

	query = '''select
					i.id as ingredient_id,
					i.name as ingredient,
					sh.id as shipment_id,
					sh.shipment_size as initial_amount,
					iis.current_amount,
					m.name as measure,
					sh.due_date,
					sh.date_supplied,
					s.name as supplier,
					st.name as supplier_type,
					st.id as supplier_type_id,
					sh.shipment_price,
					iis.is_active
				from ingredients as i
				inner join measures as m
				on i.measure_id = m.id
				inner join shipments as sh
				on sh.ingredient_id = i.id
				full outer join ingredients_in_stock as iis
				on sh.id = iis.shipment_id
				inner join suppliers as s
				on sh.supplier_id = s.id
				inner join supplier_types as st
				on st.id = s.supplier_type_id
				where ingredient_id = {} and sh.id = {}'''.format(ingredient_id, shipment_id)

	return query
