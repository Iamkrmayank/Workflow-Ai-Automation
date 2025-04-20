# ================== 📦 Install First ==================
# pip install streamlit simple_image_download requests beautifulsoup4 pandas

# ================== 📋 Import ==================
import streamlit as st
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
import csv
import time
import pandas as pd
from urllib.parse import urlparse
import io
from simple_image_download import simple_image_download as simp
import zipfile
import os
import json
import base64
import shutil

# ================== 📘 Tab Setup ==================
tab1, tab2 , tab3 , tab4 = st.tabs(["📄 Quote Scraper", " 🖼️ Bulk Image Downloader ", "🧰 CDN Image Transformer","📄 Meta Data Downloader"])
# ================== 📄 QuoteFancy Scraper in tab1 ==================
with tab1:
    st.title("📝 QuoteFancy Scraper")

    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/90.0.4430.93 Safari/537.36"
    )
    REQUEST_TIMEOUT = 10
    DELAY_BETWEEN_PAGES = 1
    MAX_PAGES = 10

    def create_session_with_retries():
        session = requests.Session()
        session.headers.update({
            'User-Agent': USER_AGENT,
            'Accept-Language': 'en-US,en;q=0.9'
        })
        retries = Retry(
            total=3,
            backoff_factor=0.3,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        adapter = HTTPAdapter(max_retries=retries)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def extract_slug_from_url(url):
        parsed = urlparse(url)
        path = parsed.path.strip("/")
        return path.split("/")[0] if path else ""

    def scrape_quotes_for_slug(slug, max_pages=MAX_PAGES):
        session = create_session_with_retries()
        rows, serial_number = [], 1

        for page_number in range(1, max_pages + 1):
            page_url = f"https://quotefancy.com/{slug}/page/{page_number}"
            try:
                response = session.get(page_url, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()
            except requests.RequestException:
                break

            soup = BeautifulSoup(response.content, "html.parser")
            containers = soup.find_all("div", class_="q-wrapper")
            if not containers:
                break

            for container in containers:
                quote_div = container.find("div", class_="quote-a")
                quote_text = quote_div.get_text(strip=True) if quote_div else container.find("a", class_="quote-a").get_text(strip=True)

                quote_link = ""
                if quote_div and quote_div.find("a"):
                    quote_link = quote_div.find("a").get("href", "")
                elif container.find("a", class_="quote-a"):
                    quote_link = container.find("a", class_="quote-a").get("href", "")

                author_div = container.find("div", class_="author-p bylines")
                if author_div:
                    author_text = author_div.get_text(strip=True).replace("by ", "").strip()
                else:
                    author_p = container.find("p", class_="author-p")
                    author_text = author_p.find("a").get_text(strip=True) if author_p and author_p.find("a") else "Anonymous"

                rows.append([serial_number, quote_text, quote_link, author_text])
                serial_number += 1

            time.sleep(DELAY_BETWEEN_PAGES)

        return rows

    def convert_to_csv_buffer(rows):
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Serial No", "Quote", "Link", "Author"])
        writer.writerows(rows)
        return output.getvalue()

    input_urls = st.text_area("Enter QuoteFancy URLs (comma separated):")
    filename = st.text_input("Filename to save as (.csv)", "quotes.csv")

    if st.button("Start Scraping", key="scrape_button"):
        if not input_urls or not filename:
            st.error("Please provide both URLs and filename.")
        else:
            url_list = [url.strip() for url in input_urls.split(",") if url.strip()]
            all_quotes = []
            for url in url_list:
                slug = extract_slug_from_url(url)
                st.write(f"🔍 Scraping: `{slug}`")
                all_quotes.extend(scrape_quotes_for_slug(slug))

            if all_quotes:
                csv_data = convert_to_csv_buffer(all_quotes)
                st.success(f"✅ Scraped {len(all_quotes)} quotes.")
                st.download_button("📥 Download CSV", data=csv_data, file_name=filename, mime='text/csv')

                df = pd.DataFrame(all_quotes, columns=["Serial No", "Quote", "Link", "Author"])
                distinct_authors = df["Author"].drop_duplicates().sort_values().tolist()
                authors_comma_str = ", ".join(distinct_authors)

                st.markdown("### 👤 Distinct Authors Found")
                st.text(authors_comma_str)
            else:
                st.warning("⚠️ No quotes scraped.")

# ================== 🖼️ Bulk Image Downloader in tab2 ==================
with tab2:

    import streamlit as st
    import boto3
    import io
    import zipfile
    import os
    import shutil
    import csv
    from simple_image_download import simple_image_download as simp
    
    # Title
    st.title("🖼️ Bulk Image Downloader + S3 CDN Uploader")
    
    # ================== 🔐 AWS Config ==================
    aws_access_key = st.secrets["aws_access_key"]
    aws_secret_key = st.secrets["aws_secret_key"]
    region_name = "ap-south-1"
    bucket_name = "suvichaarapp"
    s3_prefix = "media/"
    cdn_base_url = "https://media.suvichaar.org/"
    
    # ================== 📦 Boto3 Setup ==================
    s3 = boto3.client(
        "s3",
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key,
        region_name=region_name
    )
    
    # ================== 🎯 User Input ==================
    keywords_input = st.text_input("Enter comma-separated keywords", "cat,dog,car")
    count = st.number_input("Number of images per keyword", min_value=1, value=5)
    filename_input = st.text_input("Enter filename for CSV output", "image_links")
    
    # ================== 🚀 Main Logic ==================
    if st.button("Download & Upload Images", key="img_button"):
        keywords = [k.strip() for k in keywords_input.split(",") if k.strip()]
        response = simp.simple_image_download
    
        # Clean up old folder
        if os.path.exists("simple_images"):
            shutil.rmtree("simple_images")
    
        # ================== ⬇️ Download Images ==================
        for keyword in keywords:
            st.write(f"🔍 Downloading `{count}` images for: **{keyword}**")
            response().download(keyword, count)
    
        # ================== ☁️ Upload to S3 & Generate Links ==================
        upload_info = []
        for foldername, _, filenames in os.walk("simple_images"):
            for filename in filenames:
                filepath = os.path.join(foldername, filename)
                keyword_folder = os.path.basename(foldername)
    
                # Replace spaces with underscores
                folder_safe = keyword_folder.replace(" ", "_")
                file_safe = filename.replace(" ", "_")
                s3_key = f"{s3_prefix}{folder_safe}/{file_safe}"
    
                try:
                    s3.upload_file(filepath, bucket_name, s3_key)
                    cdn_url = f"{cdn_base_url}{s3_key}"
                    upload_info.append([folder_safe, file_safe, cdn_url])
                except Exception as e:
                    st.error(f"❌ Upload failed for {filename}: {str(e)}")
    
        # ================== 🧾 Create CSV ==================
        csv_filename = f"{filename_input.strip()}.csv"
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerow(["Keyword", "Filename", "CDN_URL"])
        writer.writerows(upload_info)
    
        # ================== 📥 Download Button ==================
        st.download_button(
            label="📥 Download CDN URLs CSV",
            data=csv_buffer.getvalue(),
            file_name=csv_filename,
            mime="text/csv"
        )
    
        st.success("✅ All images uploaded to S3 and CDN links saved!")
    
with tab3:
    
    st.title("🧰 CDN Image Transformer from CSV")

    uploaded_file = st.file_uploader("📤 Upload CSV file with `CDN_URL` column", type="csv")

    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        if "CDN_URL" not in df.columns:
            st.error("❌ The CSV must contain a column named `CDN_URL`.")
        else:
            st.success("✅ CSV Uploaded Successfully!")

            transformed_urls = []
            error_rows = []

            template = """
            {
              "bucket": "suvichaarapp",
              "key": "keyValue",
              "edits": {
                "resize": {
                  "width": 720,
                  "height": 1280,
                  "fit": "cover"
                }
              }
            }
            """

            for i, row in df.iterrows():
                media_url = row["CDN_URL"]

                try:
                    # Extract key from CDN URL
                    if not isinstance(media_url, str) or not media_url.startswith("https://media.suvichaar.org/"):
                        raise ValueError("Invalid CDN URL")

                    key_value = media_url.replace("https://media.suvichaar.org/", "")
                    json_str = template.replace("keyValue", key_value)

                    # Parse & encode the JSON
                    json_obj = json.loads(json_str)
                    encoded = base64.urlsafe_b64encode(json.dumps(json_obj).encode()).decode()

                    final_url = f"https://media.suvichaar.org/{encoded}"
                    transformed_urls.append(final_url)

                except Exception as e:
                    transformed_urls.append("ERROR")
                    error_rows.append((i, str(e)))

            # Add new column and show CSV preview
            df["Transformed_CDN_URL"] = transformed_urls

            st.markdown("### 📄 Preview of Transformed Data")
            st.dataframe(df.head())

            # Download CSV
            csv_output = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Transformed CSV", data=csv_output, file_name="transformed_cdn_links.csv", mime="text/csv")

            if error_rows:
                st.warning(f"⚠️ Some rows had errors: {len(error_rows)}")
        
with tab4:
    import re
    import random
    import string
    from datetime import datetime, timezone
    import pandas as pd
    import io
    
    # ================== 🔧 Utility Functions ==================
    def canurl(title):
        if not title or not isinstance(title, str):
            raise ValueError("Invalid title: Title must be a non-empty string.")
    
        slug = re.sub(r'[^a-z0-9-]', '', re.sub(r'\s+', '-', title.lower())).strip('-')
        alphabet = string.ascii_letters + string.digits + "_-"
        nano_id = ''.join(random.choices(alphabet, k=10)) + "_G"
        slug_nano = f"{slug}_{nano_id}"
    
        return [nano_id, slug_nano,
                f"https://suvichaar.org/stories/{slug_nano}",
                f"https://stories.suvichaar.org/{slug_nano}.html"]
    
    def generate_iso_time():
        now = datetime.now(timezone.utc)
        return now.strftime('%Y-%m-%dT%H:%M:%S+00:00')
    
    # ================== 🎯 Streamlit App ==================
    st.set_page_config(page_title="📘 Story Metadata Generator", layout="centered")
    st.title("📘 Suvichaar Story Metadata Generator")
    st.markdown("Generate structured metadata for your story titles and download as CSV or Excel.")
    
    # --- Input Fields ---
    storytitles_input = st.text_area("Enter comma-separated Story Titles", placeholder="E.g. Sunset Magic, AI-Powered Marketing")
    filename = st.text_input("Enter output filename (without extension)", value="story_metadata")
    file_format = st.selectbox("Choose output format", ["CSV (.csv)", "Excel (.xlsx)"])
    
    if st.button("Generate Metadata"):
        if not storytitles_input.strip():
            st.warning("Please enter at least one story title.")
        else:
            storytitles = [title.strip() for title in storytitles_input.split(',') if title.strip()]
            data_rows = []
    
            for storytitle in storytitles:
                uuid, urlslug, canurl_val, canurl1_val = canurl(storytitle)
                published_time = generate_iso_time()
                modified_time = generate_iso_time()
                pagetitle = f"{storytitle} | Suvichaar"
    
                data_rows.append({
                    "storytitle": storytitle,
                    "pagetitle": pagetitle,
                    "uuid": uuid,
                    "urlslug": urlslug,
                    "canurl": canurl_val,
                    "canurl 1": canurl1_val,
                    "publishedtime": published_time,
                    "modifiedtime": modified_time
                })
    
            df = pd.DataFrame(data_rows)
            st.success(f"✅ Metadata generated for {len(data_rows)} stories!")
    
            # Display preview
            st.dataframe(df)
    
            # Prepare file
            filename_clean = filename.strip() or "story_metadata"
    
            if file_format.startswith("CSV"):
                csv_buffer = io.StringIO()
                df.to_csv(csv_buffer, index=False)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv_buffer.getvalue().encode("utf-8"),
                    file_name=f"{filename_clean}.csv",
                    mime="text/csv"
                )
    
            elif file_format.startswith("Excel"):
                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name="Metadata")
                excel_buffer.seek(0)
                st.download_button(
                    label="📥 Download Excel",
                    data=excel_buffer,
                    file_name=f"{filename_clean}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
