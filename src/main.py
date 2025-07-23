import streamlit as st
from scrape import scrape_website, extract_body_content, clean_body_content, split_dom_content
from parse import parse_with_gemini
import time
from datetime import datetime
from logging_config import main_logger

# Page configuration
st.set_page_config(
    page_title="DataHarvest AI",
    page_icon="🕷️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
    }
    .status-success {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .status-error {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #007bff;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'scrape_history' not in st.session_state:
    st.session_state.scrape_history = []
if 'current_url' not in st.session_state:
    st.session_state.current_url = ""

# Main header
st.markdown("""
<div class="main-header">
    <h1>🕷️ DataHarvest AI</h1>
    <p>Intelligent Web Scraping & Data Extraction</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("📊 Dashboard")
    
    # Statistics
    if st.session_state.scrape_history:
        st.subheader("Statistics")
        total_scrapes = len(st.session_state.scrape_history)
        successful_scrapes = sum(1 for item in st.session_state.scrape_history if item['status'] == 'success')
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Scrapes", total_scrapes)
        with col2:
            st.metric("Success Rate", f"{(successful_scrapes/total_scrapes)*100:.1f}%")
    
    # Scrape History
    if st.session_state.scrape_history:
        st.subheader("Recent Activity")
        for item in st.session_state.scrape_history[-5:]:
            status_icon = "✅" if item['status'] == 'success' else "❌"
            st.write(f"{status_icon} {item['timestamp']}")
            st.caption(item['url'][:50] + "..." if len(item['url']) > 50 else item['url'])
    
    # Settings
    st.subheader("⚙️ Settings")
    chunk_size = st.slider("Chunk Size", 1000, 10000, 6000, 500)
    show_logs = st.checkbox("Show Detailed Logs", False)

# Main content
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("🌐 Website Scraper")
    
    # URL input with validation
    website_uri = st.text_input(
        "Enter Website URL",
        placeholder="https://example.com",
        help="Enter a valid URL starting with http:// or https://"
    )
    
    # URL validation
    url_valid = website_uri.startswith(('http://', 'https://')) if website_uri else False
    
    if website_uri and not url_valid:
        st.error("Please enter a valid URL starting with http:// or https://")

with col2:
    st.subheader("🎯 Quick Actions")
    col2_1, col2_2 = st.columns(2)
    
    with col2_1:
        clear_history = st.button("🗑️ Clear History", use_container_width=True)
        if clear_history:
            st.session_state.scrape_history = []
            st.success("History cleared!")
    
    with col2_2:
        if 'dom_content' in st.session_state:
            download_content = st.download_button(
                "💾 Download Content",
                st.session_state.dom_content,
                file_name=f"scraped_content_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True
            )

# Scraping section
st.subheader("🔍 Step 1: Scrape Website")

if st.button("🚀 Start Scraping", disabled=not url_valid, use_container_width=True):
    if website_uri:
        start_time = time.time()
        
        # Progress indicators
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            main_logger.info(f"User initiated scraping for: {website_uri}")
            
            # Step 1: Scraping
            status_text.text("🌐 Connecting to website...")
            progress_bar.progress(25)
            
            html_content = scrape_website(website_uri)
            
            if not html_content:
                st.error("Failed to scrape the website. Please check the URL and try again.")
                st.session_state.scrape_history.append({
                    'url': website_uri,
                    'status': 'failed',
                    'timestamp': datetime.now().strftime('%H:%M:%S'),
                    'error': 'Scraping failed'
                })
                st.stop()
            
            # Step 2: Extract body
            status_text.text("📄 Extracting content...")
            progress_bar.progress(50)
            
            body_content = extract_body_content(html_content)
            
            # Step 3: Clean content
            status_text.text("🧹 Cleaning content...")
            progress_bar.progress(75)
            
            cleaned_content = clean_body_content(body_content)
            
            # Step 4: Complete
            status_text.text("✅ Scraping completed!")
            progress_bar.progress(100)
            
            # Store results
            st.session_state.dom_content = cleaned_content
            st.session_state.current_url = website_uri
            
            elapsed_time = time.time() - start_time
            
            # Add to history
            st.session_state.scrape_history.append({
                'url': website_uri,
                'status': 'success',
                'timestamp': datetime.now().strftime('%H:%M:%S'),
                'content_length': len(cleaned_content)
            })
            
            # Success message with metrics
            st.success(f"✅ Website scraped successfully in {elapsed_time:.2f} seconds!")
            
            # Display metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Content Length", f"{len(cleaned_content):,} chars")
            with col2:
                st.metric("Processing Time", f"{elapsed_time:.2f}s")
            with col3:
                chunks = split_dom_content(cleaned_content, chunk_size)
                st.metric("Chunks Created", len(chunks))
            
            main_logger.info(f"Scraping completed successfully for {website_uri}")
            
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            main_logger.error(f"Scraping failed for {website_uri}: {str(e)}")
            st.session_state.scrape_history.append({
                'url': website_uri,
                'status': 'failed',
                'timestamp': datetime.now().strftime('%H:%M:%S'),
                'error': str(e)
            })
        finally:
            progress_bar.empty()
            status_text.empty()

# Content preview
if 'dom_content' in st.session_state:
    # Show current website info
    st.info(f"🌐 **Currently loaded:** {st.session_state.current_url}")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.subheader("📋 Scraped Content Preview")
    
    with col2:
        # Button to scrape a new website
        if st.button("🔄 Scrape New Site", use_container_width=True):
            # Clear current content to allow new scraping
            if 'dom_content' in st.session_state:
                del st.session_state.dom_content
            if 'current_url' in st.session_state:
                del st.session_state.current_url
            st.rerun()
    
    with col3:
        # Show content stats
        content_size = len(st.session_state.dom_content)
        st.metric("Content Size", f"{content_size:,} chars")
    
    with st.expander("🔍 View Full DOM Content", expanded=False):
        st.text_area(
            "Content", 
            st.session_state.dom_content, 
            height=300,
            help="This is the cleaned content extracted from the website"
        )
    
    # Parsing section
    st.subheader("🤖 Step 2: AI-Powered Data Extraction")
    
    # Add a note about multiple queries
    st.markdown("💡 **Tip:** You can ask multiple questions about the same website without re-scraping!")
    
    # Parse description input
    parse_description = st.text_area(
        "What would you like to extract?",
        placeholder="e.g., Extract all product names and prices, Get contact information, Find all email addresses...",
        help="Describe what specific information you want to extract from the scraped content"
    )
    
    # Keep track of parsing history for this session
    if 'parse_history' not in st.session_state:
        st.session_state.parse_history = []
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        parse_button = st.button("🎯 Extract Data", disabled=not parse_description.strip(), use_container_width=True)
    
    with col2:
        if st.button("💡 Examples", use_container_width=True):
            st.info("""
            **Example queries:**
            - Extract all email addresses
            - Get product names and prices
            - Find contact information
            - List all links and their text
            - Extract article titles and summaries
            """)
    
    # Show previous queries for this website
    if st.session_state.parse_history:
        with st.expander("📝 Previous Queries for This Website", expanded=False):
            for i, query in enumerate(reversed(st.session_state.parse_history[-5:]), 1):
                st.write(f"**{i}.** {query['description']}")
                st.caption(f"Asked at: {query['timestamp']}")
                if st.button(f"🔄 Re-run Query {i}", key=f"rerun_{i}"):
                    # Re-run the previous query
                    st.session_state.temp_parse_description = query['description']
                    st.rerun()
    
    # Handle re-running previous queries
    if hasattr(st.session_state, 'temp_parse_description'):
        parse_description = st.session_state.temp_parse_description
        parse_button = True
        del st.session_state.temp_parse_description
    
    if parse_button and parse_description:
        start_time = time.time()
        
        # Progress indicators
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            main_logger.info(f"User initiated parsing with description: {parse_description}")
            
            status_text.text("🔄 Preparing content chunks...")
            progress_bar.progress(20)
            
            # Split content into chunks
            dom_chunks = split_dom_content(st.session_state.dom_content, chunk_size)
            
            status_text.text(f"🤖 Processing {len(dom_chunks)} chunks with AI...")
            progress_bar.progress(40)
            
            # Parse with Gemini
            parsed_result = parse_with_gemini(dom_chunks, parse_description)
            
            status_text.text("✅ Extraction completed!")
            progress_bar.progress(100)
            
            elapsed_time = time.time() - start_time
            
            # Add to parse history
            st.session_state.parse_history.append({
                'description': parse_description,
                'timestamp': datetime.now().strftime('%H:%M:%S'),
                'result_length': len(parsed_result) if parsed_result else 0
            })
            
            if parsed_result.strip():
                st.success(f"✅ Data extracted successfully in {elapsed_time:.2f} seconds!")
                
                # Display results
                st.subheader("📊 Extracted Data")
                st.markdown("---")
                st.markdown(parsed_result)
                
                # Download button for results
                st.download_button(
                    "💾 Download Results",
                    parsed_result,
                    file_name=f"extracted_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )
                
                main_logger.info(f"Parsing completed successfully. Result length: {len(parsed_result)}")
            else:
                st.warning("No data was extracted. Try refining your description or check if the content contains the requested information.")
                main_logger.warning("Parsing completed but no results were extracted")
                
        except Exception as e:
            st.error(f"An error occurred during parsing: {str(e)}")
            main_logger.error(f"Parsing failed: {str(e)}")
        finally:
            progress_bar.empty()
            status_text.empty()

else:
    st.info("👆 Please scrape a website first to enable data extraction functionality")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>Built by Jiten! 😎</div>",
    unsafe_allow_html=True
)

# Show logs if enabled
if show_logs and 'dom_content' in st.session_state:
    with st.expander("🔍 System Logs", expanded=False):
        if st.session_state.parse_history:
            st.write("**Recent parsing activities:**")
            for query in st.session_state.parse_history[-10:]:
                st.write(f"- {query['timestamp']}: {query['description']}")
        else:
            st.text("No parsing activities yet...")