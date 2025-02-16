import streamlit as st
from googlesearch import search

st.title("Google Search for Latest Studies")

search_term = st.text_input("Enter search term (e.g., 'artificial intelligence in healthcare')")

if search_term:
    try:
        num_results = st.slider("Number of results to display", 1, 10, 5)  # Slider for number of results
        
        # Enhanced search with time range (adjust as needed)
        query = f"{search_term} (2023 OR 2024)" # Example: Search for 2023 and 2024 results.  You can customize this.
        
        search_results = list(search(query, num_results=num_results, lang="en", tld="com")) # tld for top level domain like .com, .in, etc.

        if search_results:
            st.write("Search Results:")
            for i, url in enumerate(search_results):
                st.write(f"**{i+1}. [{url}]({url})**") # Markdown link
                # You could add a short description snippet here if you want to use something like beautifulsoup4 to scrape the page.
                st.write("---")
        else:
            st.warning("No results found.")

    except Exception as e:
        st.error(f"An error occurred: {e}")
        st.info("Please check your search term and internet connection.")
