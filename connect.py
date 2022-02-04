import psycopg2
from config import config
import pandas as pd
import sql_queries as q
#import validation_lib as v

def open_connection():
    parameters = config()
    connection = psycopg2.connect(**parameters)
    return connection

def do_nothing(x): return x

def parse_post_request(request): # query_params for post request

    json = request.get_json()

    fields = []
    values = []

    for i in json:
        fields.append(i)
        values.append(json[i])

    return [fields, values]

def execute_request(query, result_format, success_status_code, query_params = [], after_execution = do_nothing, function_parameters = []):

    connection = None

    try:

        connection = open_connection()

        if query_params != []:
            query = query(*query_params)
        
        query_result = pd.read_sql_query(query, connection)

        pre_result = query_result.to_dict(orient = result_format)

        result = after_execution(pre_result, *function_parameters)

        status = success_status_code

        connection.commit()
            
    except (Exception, psycopg2.DatabaseError) as error:

        result = {"error": "{}".format(error)}
        status = 500

    finally:
            
        if connection is not None:
            connection.close()

    return result, status

def get_old_values_from(table, column, WHERE_left = None, WHERE_right = None, custom_query = None):

    connection = None

    try:

        connection = open_connection()

        if custom_query is None:

            query = q.get_column(table)
            result = pd.read_sql_query(query(column, WHERE_left, WHERE_right), connection).to_dict(orient = "list")[column]

        else:

            result = pd.read_sql_query(custom_query, connection).to_dict(orient = "list")[column]

        result_lowercase = []

        if type(result[0]) == str:
            for i in result:
                result_lowercase.append(i.lower())
            result = result_lowercase


        return result

    except (Exception, psycopg2.DatabaseError) as error:

        return error

    finally:

        if connection is not None:
            connection.close()




















































# def execute_request(request, columns_list, query, result_format, success_status_code):

#     connection = None

#     if request.is_json:

#         dictionary = request.get_json()

#         n = 0

#         query_params = []

#         while n < len(columns_list):
#             query_params.append(dictionary[columns_list[n]])
#             n += 1
#         try:
#             connection = open_connection()
#             query_result = pd.read_sql_query(query(*query_params), connection)
#             result = query_result.to_dict(orient = result_format)
#             status = success_status_code
#             connection.commit()
#         except (Exception, psycopg2.DatabaseError) as error:
#             result = {"error": "{}".format(error)}
#             status = 500
#         finally:
#             if connection is not None:
#                 connection.close()

#         return result, status

#     return {"error": "Request must be JSON"}, 400



# def execute_query(query, result_format):

#     connection = None

#     try:
#         connection = open_connection()
#         query_result = pd.read_sql_query(query, connection)
#         result = query_result.to_dict(orient = result_format)
#         connection.commit()
#         return result
#     except (Exception, psycopg2.DatabaseError) as error:
#         return {"error": "{}".format(error)}
#     finally:
#         if connection is not None:
#             connection.close()