from datetime import datetime, timedelta

import streamlit as st
from pyvalet import ValetInterpreter
import pandas as pd
vi = ValetInterpreter()

def get_currency_pairs():
    # (pd.DataFrame, pd.DataFrame) : first is group series description, second are the observations
    # [1] gets the observations
    fx_df = vi.get_group_observations("FX_RATES_DAILY", response_format='csv')[1]
    # columns are ["/r/ndate", "FXCADAUD", "FX...", ...], so return all possible FX*** values
    return fx_df.columns.tolist()[1:]

def get_exchange_rate(currency_pair, date=None):
    fx_df = vi.get_group_observations("FX_RATES_DAILY", response_format='csv')[1]
    # change the name of the 0th column from "/r/ndate" to just "date"
    fx_df = fx_df.rename(columns={fx_df.columns[0]: "date"})
    # change the type of date column from object to datetime
    fx_df["date"] = pd.to_datetime(fx_df["date"])

    if date is None:
        # if caller of the method does not provide a date, instantiate it to today's value
        date = datetime.today().strftime("%Y-%m-%d")

    # ensure date is in the datetime format
    date = pd.to_datetime(date)

    # fx_df[['date', currency_pair]] -> this means get 'date' and $currency_pair columns, drop other columns
    # then on that data frame, get rows where the date column has the provided date
    fx_date_rate = fx_df[['date', currency_pair]][fx_df['date'] == date]

    if fx_date_rate.iloc[0,1] is None:
        print("FIX ME! Find the date just before the provided date which has a value in the data frame")
        # todo
    else:
        # iloc means get the cell referenced by the row and column number, here for e.g., get cell at 0th column, 1st row
        return fx_date_rate.iloc[0,1]


def get_last_day_of_year_and_month(year, month):
    # (pd.DataFrame, pd.DataFrame) : first is group series description, second are the observations
    # [1] gets the observations
    fx_df = vi.get_group_observations("FX_RATES_DAILY", response_format='csv')[1]

    date_df = fx_df[fx_df[0]]


# Get the list of currency pairs
currency_pairs = get_currency_pairs()
currency_dict = {fx[2:5]: fx for fx in currency_pairs}
currency_list = list(currency_dict.keys())

# Streamlit UI
st.title("Salary Conversion to CAD")
entry_date = st.date_input("Entry Date in Canada:")

# RC151 requires salary calculation for past 3 years from the date of entry:
## if date of entry is 2024, tax filing would be for the year = 2024 | # so salary should be submitted for years -> 2023, 2022, 2021

entry_datetime = pd.to_datetime(entry_date)
year_of_entry = entry_datetime.year
month_of_entry = entry_datetime.month

st.markdown(f"Since you entered Canada in the year {year_of_entry} and month {month_of_entry}, you'll need to enter the income you earned in this year up till the date of your entry and your income in the years {year_of_entry-1} and {year_of_entry-2}.")



st.markdown("### Enter salary for each month & select the currency too")

months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun","Jul","Aug","Sep","Oct","Nov","Dec"]


# Initialize default values
#st.write("Enter an average monthly salary & currency below for default values:")
default_salary = st.number_input("Monthly Salary", min_value=0.0, key="amount_default")
default_currency = st.selectbox("Currency", currency_list, key="currency_default")

# Salary variation choice
salary_varies = st.checkbox("Does your salary vary each month?", value=False)

# Create input table if monthly salary varies a bit:

salaries = {}

if salary_varies:
    with st.container():
        st.markdown("### Enter salary for each month & select the currency too:")
        for month in months:
            col1, col2, col3 = st.columns([1, 1, 1])

            with col1:
                st.markdown(f"**{month}**")
            with col2:
                salaries[month] = {"amount": st.number_input(f"Amount for {month}", min_value=0.0, value=default_salary,
                                                             key=f"amount_{month}")}
            with col3:
                salaries[month]["currency"] = st.selectbox(f"Currency for {month}", currency_list,
                                                           index=currency_list.index(default_currency),
                                                           key=f"currency_{month}")
else:
    #if salary doesn't vary
    for month in months:
        salaries[month] = {"amount": default_salary, "currency": default_currency}

#button to convert salaries
if st.button("Convert to CAD"):
    st.markdown("## Converted Salaries (in CAD)")

    total_salary_cad = 0
    converted_salaries = []

    for month, data in salaries.items():
        amount = data["amount"]
        currency = data["currency"]
        currency_pair = currency_dict.get(currency, None)

        if currency_pair:
            exchange_rate, date = get_exchange_rate(currency_pair)
            if exchange_rate:
                converted_amount = round(amount * exchange_rate, 2)
                total_salary_cad += converted_amount
            else:
                converted_amount, date = "Error", "N/A"
        else:
            converted_amount, date = "Invalid Currency", "N/A"

        converted_salaries.append([month, amount, currency, converted_amount, date, exchange_rate])

    # Display results as a table
    st.table(
        [["Month", "Amount", "Currency", "Converted to CAD", "Date", "Exchange Rate"]] + converted_salaries
    )

    st.markdown(f"## Total Salary in CAD for the Year: **{total_salary_cad:,.2f}**")

