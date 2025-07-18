import streamlit as st

# streamlit UI
st.title("Data Harvest - An AI Web Scraper")
url = st.text_input("Enter Website URL")

if st.button("Scrape Website"):
    if url:
        st.write("Scraping the website...")
    else:
        st.warning("Please enter a URL")
