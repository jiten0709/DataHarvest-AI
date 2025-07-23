import streamlit as st
from scrape import (
    scrape_website,
    extract_body_content,
    clean_body_content,
    split_dom_content,
)
from parse import parse_with_gemini

# streamlit UI
st.title("Data Harvest - An AI Web Scraper")
website_uri = st.text_input("Enter Website URL")

# Step 1: Scrape the Website
if st.button("Scrape Website"):
    if website_uri:
        st.write("Scraping the website...")

        # Scrape the website
        html_content = scrape_website(website_uri=website_uri)
        body_content = extract_body_content(html_content=html_content)
        cleaned_content = clean_body_content(body_content=body_content)

        # Store the DOM content in Streamlit session state
        st.session_state.dom_content = cleaned_content

        # Display the DOM content in an expandable text box
        with st.expander("View DOM Content"):
            st.text_area("DOM Content", cleaned_content, height=300)
    else:
        st.warning("Please enter a Website URL")

# Step 2: Ask Questions About the DOM Content
if 'dom_content' in st.session_state:
    parse_description = st.text_area("Describe what you want to parse")

    if st.button("Parse Content"):
        if parse_description:
            st.write("Parsing the content...")

            # Parse the content with Gemini
            dom_chunks = split_dom_content(st.session_state.dom_content)
            parsed_result = parse_with_gemini(dom_chunks=dom_chunks, parse_description=parse_description)
            st.write(parsed_result)
        else:
            st.warning("Please provide a description of what you want to parse")
else:
    st.info("Please scrape a website first to enable parsing functionality")
    