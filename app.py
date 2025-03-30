import streamlit as st
from pyvalet import ValetInterpreter
import pandas as pd

vi = ValetInterpreter()

def get_last_market_date(fx_df, year, month, entry_date):
    """
    Returns the last available market date for the given year and month before the entry date.

    Parameters:
    - fx_df (pd.DataFrame): DataFrame with a 'date' column (datetime).
    - year (int): Target year.
    - month (int): Target month.
    - entry_date (str or datetime-like): Cutoff date.

    Returns:
    - datetime or None: Latest market date before entry_date, or None if not found.
    """
    entry_datetime = pd.to_datetime(entry_date)
    mask = (fx_df['date'].dt.year == year) & (fx_df['date'].dt.month == month) & (fx_df['date'] < entry_datetime)
    dates = fx_df.loc[mask, 'date']
    return dates.max() if not dates.empty else None

def get_currency_pairs():
    """
    Fetches the list of currency pairs from the FX_RATES_DAILY data.

    Returns:
    - list: List of currency pair column names (e.g., FXCADAUD, FXCADUSD, etc.).
    """
    fx_df = vi.get_group_observations("FX_RATES_DAILY", response_format='csv')[1]
    # columns are ["/r/ndate", "FXCADAUD", "FX...", ...], so return all possible FX*** values
    return fx_df.columns.tolist()[1:]

# Get the list of currency pairs
currency_pairs = get_currency_pairs()
currency_dict = {fx[2:5]: fx for fx in currency_pairs}
currency_list = list(currency_dict.keys())

st.header("World Income Calculation for RC151 Form")
st.caption("Based on Daily Exchange Rates from Bank of Canada :flag-ca:")
entry_date = st.date_input("# Entry Date in Canada:", min_value='2019-01-01')

entry_datetime = pd.to_datetime(entry_date)
year_of_entry = entry_datetime.year
month_of_entry = entry_datetime.month_name()

if entry_date:
    if entry_datetime.month <= 5:
        st.markdown(f"Since you entered Canada in the `{month_of_entry} {year_of_entry}`, you'll need to enter the income you earned in `{year_of_entry}` up till the date of your entry and your income in the 2 years prior, i.e., `{year_of_entry-1}` and `{year_of_entry-2}`.")
    else:
        st.markdown(f"Since you entered Canada in the `{month_of_entry} {year_of_entry}`, you'll need to enter the income you earned in {year_of_entry} up till the date of your entry and your income in the previous year, i.e., `{year_of_entry-1}`.")

st.markdown("#### Enter your salary and currency below:")

month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

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

                new_rows.append({'year': year, 'month': month, 'salary': amount_row, 'currency': currency_row})

    else:
        for month in range(1, last + 1):
            new_rows.append({'year': year, 'month': month, 'salary': default_salary, 'currency': default_currency})

salaries = pd.concat([salaries, pd.DataFrame(new_rows)], ignore_index=True)

if st.button("Convert to CAD"):
    st.markdown("## Converted Salaries (in CAD)")


    fx_df = vi.get_group_observations("FX_RATES_DAILY", response_format='csv')[1]
    # change the name of the 0th column from "/r/ndate" to just "date"
    fx_df = fx_df.rename(columns={fx_df.columns[0]: "date"})
    # change the type of date column from object to datetime
    fx_df["date"] = pd.to_datetime(fx_df["date"])

    # adding a date column from fx_df, eom_date = last market open date for the month
    salaries['eom_date'] = salaries.apply(lambda row: get_last_market_date(fx_df, row['year'], row['month'], entry_date), axis=1)

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


st.caption("**Disclaimer**: \
  \n The information provided in this tool is for informational purposes only and should not be considered legal, financial, or tax advice. While every effort has been made to ensure accuracy, I do not guarantee the completeness, reliability, or timeliness of the information presented.\
  \n Users are solely responsible for verifying the accuracy of their tax information and ensuring compliance with the Canada Revenue Agency (CRA) regulations. For personalized tax advice, please consult a qualified tax professional or accountant.\
  \n By using this tool, you acknowledge that I am not liable for any errors, omissions, or consequences arising from the use of this information.")


with st.sidebar:
    st.header("References:")

    st.link_button("→ RC151 GST/HST Credit and Canada Carbon Rebate Application", url="https://www.canada.ca/en/revenue-agency/services/forms-publications/forms/rc151.html", type = "tertiary")
    st.link_button("→ Bank of Canada Daily Exchange Rates", url="https://www.bankofcanada.ca/rates/exchange/daily-exchange-rates/", type = "tertiary")

    # Add a separator line
    st.sidebar.divider()
    st.sidebar.empty().text("")

    st.link_button(url="https://shefaliisharma.github.io", label = "Portfolio", icon=":material/link:")
    st.link_button(url="https://www.linkedin.com/in/shefaliisharma", label="LinkedIn", icon=":material/link:")
    st.link_button(url="https://github.com/shefaliisharma", label="Github", icon=":material/link:")



