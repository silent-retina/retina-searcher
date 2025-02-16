import streamlit as st
from googlesearch import search

st.title("Google Search for Latest Studies")

search_term = st.text_input("Enter search term (e.g., 'artificial intelligence in healthcare')")

if search_term:
    try:
        num_results = st.slider("Number of results to display", 1, 10, 5)

        query = f"{search_term} (2023 OR 2024)"

        search_results_generator = search(query, lang="en", tld="com")  # Get the generator

        search_results = []
        for i, url in enumerate(search_results_generator):
            if i >= num_results:  # Limit the results here
                break
            search_results.append(url)

        if search_results:
            st.write("Search Results:")
            for i, url in enumerate(search_results):
                st.write(f"**{i+1}. [{url}]({url})**")
                st.write("---")
        else:
            st.warning("No results found.")

    except Exception as e:
        st.error(f"An error occurred: {e}")
        st.info("Please check your search term and internet connection.")
