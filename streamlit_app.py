import streamlit as st
import scholarly
import requests
from bs4 import BeautifulSoup
import re
import fitz  # PyMuPDF

st.title("Automated Ophthalmology Literature Search")

# Patient Case Input
st.subheader("Patient Case Details")
keywords = st.text_area("Enter keywords describing the patient case (e.g., macular degeneration, diabetic retinopathy, etc.)")

# Google Scholar Search
st.subheader("Relevant Studies")

@st.cache_data  # Cache the search results
def perform_search(keywords):
    try:
        with st.spinner("Searching..."):
        search_query = scholarly.search_pubs(keywords)
        results = list(search_query)[:5]

        return results
    except Exception as e:
        st.error(f"Error during search: {e}")
        return []  # Return empty list in case of error


if st.button("Search"):
    if not keywords:
        st.warning("Please enter keywords to search.")
    else:
        results = perform_search(keywords)

        if results:
            for i, result in enumerate(results):
                st.write(f"**{i+1}. {result['bib']['title']}**") # Access title like this now
                st.write(f"*Authors: {result['bib'].get('author', 'N/A')}")
                st.write(f"*Journal: {result['bib'].get('journal', 'N/A')}")
                st.write(f"*Year: {result['bib'].get('year', 'N/A')}")

                if 'pub_url' in result['bib']:  # Check if pub_url exists
                    st.write(f"[Link to Paper]({result['bib']['pub_url']})")

                    # PDF Download (Improved)
                    if st.checkbox(f"Download PDF {i+1}"):
                        try:
                            response = requests.get(result['bib']['pub_url'], stream=True)
                            response.raise_for_status()

                            cd = response.headers.get('Content-Disposition')
                            if cd:
                                filename = re.findall('filename="([^"]*)"', cd)[0] if re.findall('filename="([^"]*)"', cd) else f"paper_{i+1}.pdf"
                            else:
                                filename = f"paper_{i+1}.pdf"

                            with open(filename, "wb") as f:
                                for chunk in response.iter_content(chunk_size=8192):
                                    f.write(chunk)
                            st.success(f"PDF {i+1} downloaded as {filename}!")
                        except requests.exceptions.RequestException as e:
                            st.error(f"Error downloading PDF: {e}")
                        except Exception as e:
                            st.error(f"Error processing PDF: {e}")

                st.write("---")
        else:
            st.info("No results found.")


# ... (rest of the code for Further Reading and PDF Content Extraction as before)
# Further Reading (Placeholder)
st.subheader("Further Reading")
st.write("This section could include links to relevant ophthalmology resources, databases, or other tools.")


# PDF Content Extraction (Basic Example - Requires PDF parsing library)
# (This is a complex task and would require a dedicated PDF parsing library like PyPDF2, PyMuPDF, or similar)
st.subheader("PDF Content Extraction (Experimental)")
uploaded_file = st.file_uploader("Upload a PDF", type="pdf")
if uploaded_file is not None:
    try:
        # ... (PDF parsing logic using chosen library)
        # Example (using PyMuPDF - you'd need to install it: pip install pymupdf)
        import fitz # PyMuPDF
        doc = fitz.open(uploaded_file)
        text = ""
        for page in doc:
            text += page.get_text()

        #Clean text from special characters
        cleaned_text = re.sub(r'[^\x00-\x7F]+', '', text) #remove non-ascii

        st.write(cleaned_text[:500] + "...") # Display a snippet

    except Exception as e:
        st.error(f"Error processing PDF: {e}")
