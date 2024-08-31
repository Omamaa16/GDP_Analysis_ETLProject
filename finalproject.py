import glob
import pandas as pd
import numpy as n
from datetime import datetime as d
import sqlite3 as s
from bs4 import BeautifulSoup as b
import requests
import sqlite3

# WEB SCRAPING AND EXTRACTION
def extraction(url):
    h = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36", "Accept-Langauge": "en-US", "en": "q=0.5"}
    htmlpage = requests.get(url, headers=h)
    parsing_htmlpage = b(htmlpage.text, "html.parser")

    table = parsing_htmlpage.find_all("table", id="")
    table = table[2]

    headers = table.find_all("th")
    title = []
    for i in headers:
        titles = i.text
        title.append(titles)
    columns = [title[0].strip("\n"), title[5]]
    data_column = pd.DataFrame(columns=columns)
    data_column.rename(columns={"Estimate": "IMF Estimate"}, inplace=True)

    rows = table.find_all("tr")
    r = []
    for j in rows[1:]:
        data = j.find_all("td")
        row_data = [x.text for x in data]
        r.append(row_data)
    df = pd.DataFrame(r)
    data_row = df.iloc[:, [0, 2]]

    x = pd.concat([data_column, data_row], axis=0)
    x['Country/Territory'] = x['Country/Territory'].fillna(df[0])
    x['IMF Estimate'] = x['IMF Estimate'].fillna(df[2])
    x.drop(columns=[0, 2], inplace=True)
    x = x.drop(x.index[0])

    return x

#TRANSFORMATION
def transformation(data):

    #checking for the "--" and replacing it with the mode
    if (data["Country/Territory"]=="—").any(): 
       data["Country/Territory"].replace("—", data["Country/Territory"].mode()[0])

    #checking for the "--" and replacing it with the mean
    if (data["IMF Estimate"]=="—").any():
        data["IMF Estimate"] = data["IMF Estimate"].str.replace(",","")
        data["IMF Estimate"] = pd.to_numeric(data["IMF Estimate"], errors="coerce")
        data["IMF Estimate"] = data["IMF Estimate"].fillna(data["IMF Estimate"].mean())

    #converting the values to float
    data["IMF Estimate"] = data["IMF Estimate"].astype(float)

    #dividing the values by 10
    data["IMF Estimate"] = round((data["IMF Estimate"]/10),2)

    #renaming the column name
    data.rename(columns={"IMF Estimate":"GDP_USD_billions"}, inplace=True) 

    return data

#LOADING
def load(transformeddata):
    transformeddata.to_csv("project.csv")
    return transformeddata

#SQL connection
def SQL(dataframe):
    conn = sqlite3.connect("MyDB.db")
    table = "GDP_by_Country"

    dataframe.to_sql(table, conn, if_exists="replace", index=False)

    query = f"SELECT * FROM {table} LIMIT 5"
    result = pd.read_sql(query, conn)

    return result

#Logging
def log(message):
    date_format = '%Y-%h-%d-%H:%M:%S'
    current_time = d.now()
    formatted_date = current_time.strftime(date_format)
    with open("etl_project_log.txt","a") as file:
        file.write(formatted_date + ' : ' + message + '\n')

    return message

extracted_data = extraction("https://web.archive.org/web/20230902185326/https://en.wikipedia.org/wiki/List_of_countries_by_GDP_%28nominal%29")
print(extracted_data)

logged_details = log("Extracted")
print(logged_details)

transformed_data=transformation(extracted_data)
print(transformed_data)

logged_details = log("Transformed")
print(logged_details)

loaded_data = load(transformed_data)
print(loaded_data)

logged_details = log("Loaded")
print(logged_details)

query_result = SQL(loaded_data)
print(query_result)

logged_details = log("Loaded in the SQL")
print(logged_details)
