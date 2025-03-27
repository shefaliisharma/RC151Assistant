import streamlit as st
import requests
import xml.etree.ElementTree as ET

# API URL for currency pairs
FX_API_URL = "https://www.bankofcanada.ca/valet/fx_rss"

# Define the RDF namespace
namespaces = {
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "ns1": "http://purl.org/rss/1.0/",  # Mapping ns1 prefix to its URI
    "dc": "http://purl.org/dc/elements/1.1/",
    "ns3": "http://www.cbwiki.net/wiki/index.php/Specification_1.1"
}


def get_currency_pairs():
    # Fetch available currency pairs from Bank of Canada API
    response = requests.get(FX_API_URL)
    xml_data = ET.fromstring(response.content)


    # Extract the currency pairs (series) from the XML using the correct namespace
    # The currency pairs should be in rdf:li elements, and we need to check for their rdf:resource attribute
    series = []
    for item in xml_data.findall(".//rdf:li", namespaces):
        resource_url = item.attrib.get("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource", "")
        series_code = resource_url.split("/")[-1]  # Extract series code from the URL
        series.append(series_code)
    return series


def get_exchange_rate(currency_pair):
    # Fetch the XML data for the selected currency pair
    pair_url = f"https://www.bankofcanada.ca/valet/fx_rss/{currency_pair}"
    response = requests.get(pair_url)
    xml_data = ET.fromstring(response.content)

    # Print the XML structure for debugging (this helps us understand the actual structure)
    #print(ET.tostring(xml_data, encoding="unicode"))

    # Extract exchange rate and date from the title using the correct namespace
    exchange_rate_text = xml_data.find(".//ns1:item/ns3:statistics/ns3:exchangeRate/ns3:value", namespaces).text
    exchange_rate = float(exchange_rate_text)
    date = xml_data.find(".//ns1:item/dc:date", namespaces).text

    return exchange_rate, date



# Streamlit UI
st.title("Currency Exchange Rate")
st.markdown("### Select a Currency Pair")

# Get the list of currency pairs
currency_pairs = get_currency_pairs()

# Dropdown to select the currency pair
currency_pair = st.selectbox("Choose a currency pair:", currency_pairs)

# Button to get the exchange rate
if st.button('Get Exchange Rate'):
    # Get exchange rate and date for the selected pair
    if currency_pair:
        exchange_rate, date = get_exchange_rate(currency_pair)

        # Display exchange rate and date
        st.markdown(f"### Exchange Rate: **{exchange_rate}**")
        st.markdown(f"### Date: **{date}**")
