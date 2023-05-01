import math
import statistics
import certifi
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from pymongo.mongo_client import MongoClient


def get_mongo_dataframe():
    """
    establish connection w/ MongoClient;
    take out specific columns for ML model;
    returns pd dataframe of relevant data - drop _id col
    """
    # creating connection
    client = MongoClient(
            "mongodb+srv://beepmrw:Beepm@beepm1.21uirez.mongodb.net/test?retryWrites=true&w=majority&ssl=true",
                tlsCAFile=certifi.where())
    client.admin.command('ping')

    # creating dataframe from requested info
    columns = {'Primary Property Type - Self Selected', 'Occupancy', 'Number of Buildings',
               'Self-Reported Gross Floor Area (ft²)', 'Total GHG Emissions (Metric Tons CO2e)', 'Electricity Use'}
    cursor_list = list(client.beepm_data["ll84"].find({}, columns))
    df = pd.DataFrame(cursor_list)
    df.drop('_id', axis=1, inplace=True)
    return df


def get_building_types(dataframe, minimum):
    """
    gets building types from dataframe with at least
    minimum number of instances.
    type of building assumed to be at column [1] of dataframe
    """
    # counting each type of building in df
    building_types, ret_types = dict(), dict()
    for index in range(len(dataframe)):
        if dataframe.iloc[index][1] in building_types:
            building_types[dataframe.iloc[index][1]] += 1
        else:
            building_types[dataframe.iloc[index][1]] = 1
    
    # returning those with minimum number of entries
    for item in building_types:
        if building_types[item] > minimum:
            ret_types[item] = building_types[item]
    return ret_types


def clean_dataframe(dataframe, column):
    """
    column is var to be predicted
    all np.nan are removed
    creates multiple exponential regression for provided data
    """
    # getting rid of all rows containing np.nan - useless for training
    for column in dataframe.columns:
        dataframe = dataframe[dataframe[column].notna()]

    # prevent division by zero in calculations
    dataframe = dataframe[dataframe[column] > 0]

    # separate X (df) and Y (GHG)
    y = np.array(dataframe.pop(column)).reshape(-1, 1)
    x = np.array(dataframe)

    # exponential regression via normalizing all pred vals
    regression = LinearRegression().fit(x, [math.log(val) for val in y])
    return dataframe, regression, y


def predict_data(dataframe, regression, percent_outlier, y):
    """
    collects actual and expected vals for each row;
    this is the ML model
    """
    # gathering information
    expected, actual = [], []
    errors, outliers = [], []

    # making predictions for each non-np.nan entry
    for index in range(len(dataframe)):
        prediction = np.array(dataframe.iloc[index]).reshape(1, -1)
        predEm = regression.predict(prediction)[0]
        predEm = math.e ** predEm

        error = abs((y[index][0] - predEm) / y[index][0] * 100)
        expected.append(predEm)
        actual.append(y[index][0])

        # outliers... unless?
        if error < percent_outlier:
            errors.append(error)

#             print('PREDICTED GHG EMISSIONS:', predEm)
#             print('ACTUAL GHG EMISSIONS:', y[index][0])
#             print('ABS PERCENT ERROR:', error, '%')
#             print()
        else:
            outliers.append(error)
#     print('Average error is', round(sum(errors) / len(errors)), '%')
#     print(len(outliers), 'outliers;', round(len(outliers) / len(dataframe) * 100, 2), '% of total entries')
#     print('Outlier error ranges from', round(min(outliers)), '% to', round(max(outliers)), '%')
    return dataframe, expected, actual


def find_letter_grade(val):
    
    if val < -1.66:
        return 'F'
    elif val < -1.33:
        return 'D-'
    elif val < -1:
        return 'D'
    elif val < -0.66:
        return 'D+'
    elif val < -0.33:
        return 'C-'
    elif val < 0:
        return 'C'
    elif val < 0.33:
        return 'C+'
    elif val < 0.66:
        return 'B-'
    elif val < 1.0:
        return 'B'
    elif val < 1.33:
        return 'B+'
    elif val < 1.66:
        return 'A'
    else:
        return 'A+'
    

def evaluate(pred_score, avg_score, deviation):
    """
    returns letter grade for pred_score
    """
    return (avg_score - pred_score) / deviation


def get_prediction(building_type, occupation, num_buildings, area):
    """
    makes prediction based on parameters;
    returns letter grade for proposed building
    """
    variables = ['Total GHG Emissions (Metric Tons CO2e)', 'Electricity Use']
    df = get_mongo_dataframe()
    grades, vals, averages = list(), list(), list()
    
    for v in variables:
        cols = [var for var in variables if var != v]
        copydf = df.drop(cols, axis=1)

        types = get_building_types(copydf, 1000)
        if building_type not in types:
            raise BaseException('Building type DNE; choose one of ', types)
        
        try:
            copydf = copydf[copydf['Primary Property Type - Self Selected'].str.contains(building_type) == True]
            copydf = copydf.drop('Primary Property Type - Self Selected', axis=1)
            copydf, regression, y = clean_dataframe(copydf, v)
            copydf, expected, actual = predict_data(copydf, regression, 300, y)
            
            prediction = np.array([area, num_buildings, occupation]).reshape(1, -1)
            predEm = regression.predict(prediction)[0]
            predEm = math.e ** predEm
            
            grades.append(evaluate(math.log(predEm), sum([math.log(a) for a in actual]) / len(actual),
                    statistics.stdev([math.log(a) for a in actual])))
            averages.append(math.e ** (sum([math.log(a) for a in actual]) / len(actual)))
            vals.append(predEm)

        except Exception as e:
            print(e)
            raise(e)
        
    return find_letter_grade(sum(grades) / len(grades)), vals, averages


def get_analysis(prediction):
    """
    simple assessment of prediction;
    to be displayed to frontend
    """
    ret = list()
    ret.append('The building scores ' + prediction[0] + ' ')
    
    emissionsCompare = prediction[1][0] / prediction[2][0]
    if emissionsCompare < 1:
        ret.append('GHS emissions rate is ' + str(abs(round(1 - emissionsCompare * 100))) + \
            ' percent less than the average for its building type')
    else:
        ret.append('GHS emissions rate is ' + str(abs(round(1 - emissionsCompare * 100))) + \
            ' percent more than the average for its building type')
    
    electricCompare = prediction[1][1] / prediction[2][1]
    if electricCompare < 1:
        ret.append('Electricity usage is ' + str(abs(round(1 - electricCompare * 100))) + \
        ' percent less than the average for its building type')
    else:
        ret.append('Electricity usage is ' + str(abs(round(1 - electricCompare * 100))) + \
            ' percent more than the average for its building type')
    return ret
