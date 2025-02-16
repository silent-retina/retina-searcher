import streamlit as st
import scholarly

st.title("Academic Publication Search")

search_term = st.text_input("Enter search term (e.g., 'machine learning')")

if search_term:
    try:
        # Use the updated search method (example)
        search_results = scholarly.search_pubs(search_term)  # Or try search_author, etc.

        # Display results (adjust as needed)
        st.write("Search Results:")
        for publication in search_results:
            st.write(f"**{publication.bib['title']}**")
            # st.write(f"Authors: {publication.bib['author']}") # Access other fields as needed
            # st.write(f"Year: {publication.bib['year']}")
            # st.write(f"Abstract: {publication.bib['abstract']}")
            st.write("---")

    except Exception as e:
        st.error(f"An error occurred: {e}")
        st.info("Please ensure the 'scholarly' library is updated and that the search term is valid.  The API for scholarly may have changed.  Consult the library's documentation for the most up-to-date usage.")
