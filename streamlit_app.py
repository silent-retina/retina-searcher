import streamlit as st
import pandas as pd
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import json
from io import BytesIO
import google.generativeai as genai
import plotly.express as px

class PubMedAPI:
    def __init__(self):
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        self.tool_name = "ophth_case_assistant"
        self.email = "anandsinghbrar@proton.me"
        
    def generate_search_query(self, patient_scenario, model):
        """Generate PubMed search query from patient scenario using LLM"""
        prompt = f"""
        Given this ophthalmology patient scenario: {patient_scenario}
        
        Generate a PubMed search query that will find relevant research articles. 
        Focus on key clinical features, possible diagnoses, and treatment approaches.
        Use proper PubMed syntax with [MeSH Terms] containing the diagnosis with OR operators.
        Return only the search query without any explanation.
        """
        
        response = model.generate_content(prompt)
        return response.text.strip()
        
    def search_studies(self, query, max_results=20):
        """Search PubMed for studies"""
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
            article_data = {
                "pmid": article.find(".//PMID").text,
                "title": article.find(".//ArticleTitle").text or "No title available",
                "abstract": "",
                "authors": [],
                "journal": "",
                "publication_date": "",
                "keywords": []
            }
            
            abstract_elem = article.find(".//Abstract/AbstractText")
            if abstract_elem is not None:
                article_data["abstract"] = abstract_elem.text or ""
                
            author_list = article.findall(".//Author")
            for author in author_list:
                last_name = author.find("LastName")
                fore_name = author.find("ForeName")
                if last_name is not None and fore_name is not None:
                    author_data = f"{last_name.text} {fore_name.text}"
                    article_data["authors"].append(author_data)
                    
            journal_elem = article.find(".//Journal/Title")
            if journal_elem is not None:
                article_data["journal"] = journal_elem.text
                
            pub_date = article.find(".//PubDate")
            if pub_date is not None:
                year = pub_date.find("Year")
                if year is not None:
                    article_data["publication_date"] = year.text
                    
            keyword_list = article.findall(".//Keyword")
            article_data["keywords"] = [k.text for k in keyword_list if k.text]
            
            return article_data
            
        except Exception as e:
            st.error(f"Error parsing article: {str(e)}")
            return None

def generate_clinical_summary(patient_scenario, studies, model):
    """Generate a clinical summary of relevant studies using LLM"""
    studies_text = "\n\n".join([
        f"Title: {study['title']}\nAbstract: {study['abstract']}"
        for study in studies[:5]  # Limit to top 5 studies for conciseness
    ])
    
    prompt = f"""
    Patient Scenario:
    {patient_scenario}
    
    Relevant Studies:
    {studies_text}
    
    Please provide a concise clinical summary that:
    1. Identifies key findings from these studies relevant to the patient case
    2. Highlights any treatment recommendations or clinical guidelines
    3. Notes important considerations or limitations
    
    Format the response in clear sections with bullet points for key takeaways.
    """
    
    response = model.generate_content(prompt)
    return response.text

def export_to_excel(studies):
    """Export studies to Excel file"""
    df = pd.DataFrame(studies)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Studies')
    return output.getvalue()

def main():
    st.set_page_config(page_title="Ophthalmology Case Literature Assistant", layout="wide")
    
    # Configure Google API
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("GOOGLE_API_KEY not found in secrets.")
        st.stop()
    
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    # Initialize PubMed API
    pubmed_api = PubMedAPI()
    
    st.title("🔍 Ophthalmology Case Literature Assistant")
    
    # Patient scenario input
    st.header("Patient Scenario")
    patient_scenario = st.text_area(
        "Enter Patient Details",
        placeholder="Describe the patient's case including:\n- Age and gender\n- Presenting symptoms\n- Relevant history\n- Examination findings\n- Any test results",
        height=200
    )
    
    max_results = st.slider("Maximum Number of Studies", 5, 50, 20)
    
    if st.button("Find Relevant Literature", type="primary"):
        if patient_scenario:
            with st.spinner("Analyzing case and searching literature..."):
                # Generate search query from patient scenario
                search_query = pubmed_api.generate_search_query(patient_scenario, model)
                st.write("Generated PubMed Query:", search_query)
                
                # Search for relevant studies
                studies = pubmed_api.search_studies(search_query, max_results)
                
                if studies:
                    # Generate clinical summary
                    st.header("Clinical Summary")
                    summary = generate_clinical_summary(patient_scenario, studies, model)
                    st.markdown(summary)
                    
                    # Display results count and export button
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.subheader(f"Found {len(studies)} relevant studies")
                    with col2:
                        excel_data = export_to_excel(studies)
                        st.download_button(
                            "📥 Export to Excel",
                            excel_data,
                            file_name=f"ophth_case_studies_{datetime.now().strftime('%Y%m%d')}.xlsx",
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
                    
                    # Display individual studies
                    st.header("Detailed Study Information")
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
                    st.warning("No relevant studies found. Try modifying the patient scenario with more clinical details.")
        else:
            st.warning("Please enter a patient scenario to search for relevant literature.")

if __name__ == "__main__":
    main()
