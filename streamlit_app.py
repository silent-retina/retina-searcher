import streamlit as st
import pandas as pd
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import json
from io import BytesIO
import time
from urllib.parse import quote_plus
import plotly.express as px

class PubMedAPI:
    def __init__(self):
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        self.tool_name = "ophth_literature_tool"
        self.email = "anandsinghbrar@proton.me"  # Replace with actual email
        
    def search_studies(self, query, max_results=20):
        """Search PubMed for studies"""
        # First get article IDs
        search_url = f"{self.base_url}esearch.fcgi"
        params = {
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "sort": "relevance",
            "tool": self.tool_name,
            "email": self.email,
            "retmode": "json"
        }
        
        try:
            response = requests.get(search_url, params=params)
            response.raise_for_status()
            search_results = response.json()
            
            if 'esearchresult' in search_results:
                id_list = search_results['esearchresult'].get('idlist', [])
                return self.fetch_article_details(id_list)
            return []
            
        except requests.exceptions.RequestException as e:
            st.error(f"Error searching PubMed: {str(e)}")
            return []
            
    def fetch_article_details(self, id_list):
        """Fetch detailed information for articles by their PMIDs"""
        if not id_list:
            return []
            
        fetch_url = f"{self.base_url}efetch.fcgi"
        params = {
            "db": "pubmed",
            "id": ",".join(id_list),
            "retmode": "xml",
            "tool": self.tool_name,
            "email": self.email
        }
        
        try:
            response = requests.get(fetch_url, params=params)
            response.raise_for_status()
            
            # Parse XML response
            root = ET.fromstring(response.content)
            articles = []
            
            for article in root.findall(".//PubmedArticle"):
                article_data = self._parse_article(article)
                if article_data:
                    articles.append(article_data)
                    
            return articles
            
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching article details: {str(e)}")
            return []
            
    def _parse_article(self, article):
        """Parse individual article XML"""
        try:
            # Extract basic article information
            article_data = {
                "pmid": article.find(".//PMID").text,
                "title": article.find(".//ArticleTitle").text or "No title available",
                "abstract": "",
                "authors": [],
                "journal": "",
                "publication_date": "",
                "keywords": []
            }
            
            # Get abstract
            abstract_elem = article.find(".//Abstract/AbstractText")
            if abstract_elem is not None:
                article_data["abstract"] = abstract_elem.text or ""
                
            # Get authors
            author_list = article.findall(".//Author")
            for author in author_list:
                last_name = author.find("LastName")
                fore_name = author.find("ForeName")
                if last_name is not None and fore_name is not None:
                    author_data = f"{last_name.text} {fore_name.text}"
                    article_data["authors"].append(author_data)
                    
            # Get journal info
            journal_elem = article.find(".//Journal/Title")
            if journal_elem is not None:
                article_data["journal"] = journal_elem.text
                
            # Get publication date
            pub_date = article.find(".//PubDate")
            if pub_date is not None:
                year = pub_date.find("Year")
                if year is not None:
                    article_data["publication_date"] = year.text
                    
            # Get keywords
            keyword_list = article.findall(".//Keyword")
            article_data["keywords"] = [k.text for k in keyword_list if k.text]
            
            return article_data
            
        except Exception as e:
            st.error(f"Error parsing article: {str(e)}")
            return None

def export_to_excel(studies):
    """Export studies to Excel file"""
    df = pd.DataFrame(studies)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Studies')
    return output.getvalue()

def main():
    st.set_page_config(page_title="Ophthalmology Literature Search", layout="wide")
    
    # Initialize PubMed API
    pubmed_api = PubMedAPI()
    
    # Custom CSS for better UI
    st.markdown("""
        <style>
        .stAlert {margin-top: 1rem;}
        .study-card {
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 1rem 0;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Title with icon
    st.title("🔍 Ophthalmology Literature Search Assistant")
    
    # Create tabs for different sections
    search_tab, saved_tab = st.tabs(["Search Studies", "Saved Results"])
    
    with search_tab:
        # Side panel for search criteria
        with st.sidebar:
            st.header("Search Criteria")
            
            # Basic search options
            search_type = st.radio("Search Type", ["Condition-based", "Custom Query"])
            
            if search_type == "Condition-based":
                conditions = st.multiselect(
                    "Select Conditions",
                    [
                        "Diabetic Retinopathy",
                        "Glaucoma",
                        "Age-related Macular Degeneration",
                        "Cataracts",
                        "Dry Eye Disease",
                        "Retinal Detachment"
                    ]
                )
                
                # Additional filters
                study_type = st.multiselect(
                    "Study Type",
                    ["Clinical Trial", "Review", "Case Report", "Meta-Analysis"]
                )
                
                year_range = st.slider(
                    "Publication Year",
                    min_value=2000,
                    max_value=datetime.now().year,
                    value=(2015, datetime.now().year)
                )
                
                max_results = st.slider("Maximum Results", 5, 50, 20)
                
                # Build search query
                if conditions:
                    query_parts = [
                        f"({' OR '.join(conditions)})",
                        "ophthalmology[MeSH Terms]"
                    ]
                    if study_type:
                        query_parts.append(f"({' OR '.join([f'{t}[Publication Type]' for t in study_type])})")
                    query_parts.append(f"{year_range[0]}:{year_range[1]}[Publication Date]")
                    search_query = " AND ".join(query_parts)
                else:
                    search_query = ""
                
            else:
                search_query = st.text_area(
                    "Enter Search Query",
                    placeholder="Enter PubMed search query (e.g., 'diabetic retinopathy AND treatment')"
                )
                max_results = st.slider("Maximum Results", 5, 50, 20)
        
        # Main content area
        if st.button("Search Literature", type="primary"):
            if search_query:
                with st.spinner("Searching PubMed..."):
                    studies = pubmed_api.search_studies(search_query, max_results)
                    
                    if studies:
                        # Display results count and export button
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.subheader(f"Found {len(studies)} relevant studies")
                        with col2:
                            excel_data = export_to_excel(studies)
                            st.download_button(
                                "📥 Export to Excel",
                                excel_data,
                                file_name=f"ophth_studies_{datetime.now().strftime('%Y%m%d')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                        
                        # Create visualization of publication years
                        years = [study.get('publication_date') for study in studies if study.get('publication_date')]
                        if years:
                            year_counts = pd.Series(years).value_counts().sort_index()
                            fig = px.bar(
                                x=year_counts.index,
                                y=year_counts.values,
                                title="Publication Year Distribution",
                                labels={'x': 'Year', 'y': 'Number of Studies'}
                            )
                            st.plotly_chart(fig)
                        
                        # Display studies
                        for i, study in enumerate(studies, 1):
                            with st.expander(f"{i}. {study['title']}", expanded=i==1):
                                col1, col2 = st.columns([3, 1])
                                
                                with col1:
                                    st.markdown(f"**Authors:** {', '.join(study['authors'][:3])}{'...' if len(study['authors']) > 3 else ''}")
                                    st.markdown(f"**Journal:** {study['journal']}")
                                    st.markdown(f"**Publication Date:** {study['publication_date']}")
                                    if study['abstract']:
                                        st.markdown("**Abstract:**")
                                        st.markdown(study['abstract'])
                                    
                                with col2:
                                    st.markdown("### Quick Links")
                                    st.markdown(f"[PubMed Link](https://pubmed.ncbi.nlm.nih.gov/{study['pmid']})")
                                    if study['keywords']:
                                        st.markdown("**Keywords:**")
                                        st.markdown(", ".join(study['keywords']))
                    else:
                        st.warning("No studies found matching your criteria.")
            else:
                st.warning("Please enter a search query or select conditions to search.")
    
    with saved_tab:
        st.info("Feature coming soon: Save and organize your favorite studies!")

if __name__ == "__main__":
    main()
