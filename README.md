## RC151 Assistant
A Streamlit app that calculates world income in CAD for the CRA's RC151 (GST/HST Credit and Canada Carbon Rebate) application.
Users enter their date of arrival in Canada, then input salary by year, month, and currency. The app determines which years of income the CRA requires based on entry date, pulls live daily FX rates from the Bank of Canada's Valet API (via _pyvalet_), matches each income entry to the last available market-open exchange rate before the relevant date, and converts everything to CAD — producing a year-by-year summary and a full transaction-level breakdown.

#### Key logic:
* Encodes CRA's actual reporting rule (3 prior years if entry is before June 1, 2 prior years otherwise)
* Resolves income dates to the correct trading-day FX rate, handling weekends/holidays when no rate is published
* Supports variable monthly salary and variable currency per month
* Aggregates multi-year, multi-currency income into a single CAD summary

##### Stack: Python, Streamlit, pandas, pyvalet (Bank of Canada Valet API)


[See demo](https://rc151assistant.streamlit.app)
