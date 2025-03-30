from datetime import datetime, timedelta

import streamlit as st
from pyvalet import ValetInterpreter
import pandas as pd
vi = ValetInterpreter()

def get_last_market_date(fx_df, year, month):
    mask = (fx_df['date'].dt.year == year) & (fx_df['date'].dt.month == month)
    dates = fx_df.loc[mask, 'date']
    return dates.max() if not dates.empty else None
def get_currency_pairs():
    # (pd.DataFrame, pd.DataFrame) : first is group series description, second are the observations
    # [1] gets the observations
    fx_df = vi.get_group_observations("FX_RATES_DAILY", response_format='csv')[1]
    # columns are ["/r/ndate", "FXCADAUD", "FX...", ...], so return all possible FX*** values
    return fx_df.columns.tolist()[1:]




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



st.markdown("## Enter salary for each month & select the currency too")

month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

# Initialize default values
#st.write("Enter an average monthly salary & currency below for default values:")


salaries = pd.DataFrame(columns=['year', 'month', 'salary', 'currency'])

new_rows = []

# step_year: world income in RC151 is needed for past 3 years
step_year = 3

# only if you became a resident of Canada between January 1 and May 31 of the year you entered
if entry_date.month > 5:
    step_year = 2

for year in range(entry_date.year, entry_date.year - step_year, -1):
    st.markdown(f"### Year {year}")
    default_salary = st.number_input(f"Monthly Salary in year {year}", min_value=0.0, key=f"amount_default_{year}")
    default_currency = st.selectbox("Currency", currency_list, key=f"currency_default_{year}")
    # Salary variation choice
    salary_varies = st.checkbox("Does your salary vary each month?", value=False, key=f"salary_varies_{year}")
    last = 12
    if year == entry_date.year:
        if entry_date.day == 1:
            last = entry_date.month - 1
        else:
            last = entry_date.month
    if salary_varies:
        # Create input table if monthly salary varies a bit:

        with st.container():
            st.markdown("### Enter salary for each month & select the currency too:")
            for month in range(1, last + 1):
                col1, col2, col3 = st.columns([1, 1, 1])
                month_name = month_names[month - 1]
                with col1:
                    st.markdown(f"**{month_name}**")
                with col2:
                    amount_row = st.number_input(f"Amount for {month_name}", min_value=0.0, value=default_salary,
                                                  key=f"amount_{month}_{year}")
                with col3:
                    currency_row = st.selectbox(f"Currency for {month_name}", currency_list,
                                                               index=currency_list.index(default_currency),
                                                               key=f"currency_{month}_{year}")
                #appending row
                new_rows.append({'year': year, 'month': month, 'salary': amount_row, 'currency': currency_row})

    else:
        for month in range(1, last + 1):
            new_rows.append({'year': year, 'month': month, 'salary': default_salary, 'currency': default_currency})

salaries = pd.concat([salaries, pd.DataFrame(new_rows)], ignore_index=True)


#button to convert salaries
if st.button("Convert to CAD"):
    st.markdown("## Converted Salaries (in CAD)")

    # load the fx_df dataframe, fx_df = FX_RATES_DAILY from Bank of Canada
    fx_df = vi.get_group_observations("FX_RATES_DAILY", response_format='csv')[1]
    # change the name of the 0th column from "/r/ndate" to just "date"
    fx_df = fx_df.rename(columns={fx_df.columns[0]: "date"})
    # change the type of date column from object to datetime
    fx_df["date"] = pd.to_datetime(fx_df["date"])
    print(salaries)
    # adding a date column from fx_df, eom_date = last market open date for the month
    salaries['eom_date'] = salaries.apply(lambda row: get_last_market_date(fx_df, row['year'], row['month']), axis=1)

    # for eom_date, fetch the exchange rate from fx_df
    salaries['exchange_rate'] = salaries.apply(
        lambda row: fx_df.loc[fx_df['date'] == row['eom_date'], f"FX{row['currency']}CAD"].values[0]
        if row['eom_date'] is not None else None, axis=1)

    #now convert the salaries to CAD
    salaries['Salaries in CAD'] = salaries['salary'] * salaries['exchange_rate']

    # display the salaries by Year
    df_summary = salaries.groupby('year', as_index=False)['Salaries in CAD'].sum()

    st.dataframe(df_summary.style.format({
        'Salaries in CAD': "CAD   {:,.2f}"
    }))
    with st.expander("See Full Salary Table"):
        st.dataframe(salaries)






