import pandas as pd
import re
from tqdm import tqdm
import nltk
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('punkt')
from nltk.corpus import stopwords
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import streamlit as st
import pickle
from sklearn import preprocessing  # Impor preprocessing


# Fungsi untuk menginisialisasi web driver
# def web_driver():
#     options = Options()
#     options.add_argument('--headless')  # Uncomment if you don't want a UI
#     options.add_argument('--no-sandbox')
#     options.add_argument('--disable-dev-shm-usage')

#     driver = webdriver.Chrome(options=options)
#     return driver

def web_driver():
    options = EdgeOptions()
    options.add_argument('--headless')  # Hapus jika ingin mode dengan UI
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    # Tentukan versi Edge sesuai dengan versi yang terinstal
    service = EdgeService(EdgeChromiumDriverManager(version="115.0.1901.188").install())
    driver = webdriver.Edge(service=service, options=options)
    return driver

# Fungsi untuk mengambil teks dari elemen web
def get_element_text(driver, xpath):
    try:
        return WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        ).text.strip()
    except Exception as e:
        print(f"Error finding element with XPath {xpath}: {e}")
        return ""


# Fungsi untuk mengambil konten artikel
def extract_article_content(driver, article_url):
    driver.get(article_url)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//h1'))
    )
    title = get_element_text(driver, './/h1')
    date = get_element_text(driver, './/p[@class="pt-20 date"]')
    content_elements = driver.find_elements(By.XPATH, './/div[@class="news-text"]/p')
    content = " ".join(p.text for p in content_elements)
    kategori = get_element_text(driver, './/div[@class="breadcrumb-content"]/p')

    return {
        "Title": title,
        "Date": date,
        "Content": content,
        "Category": kategori
    }

# Fungsi untuk membersihkan teks
def clean_lower(text):
    return text.lower() if isinstance(text, str) else text

def clean_punct(text):
    clean_patterns = re.compile(r'[0-9]|[/(){}\[\]\|@,;_]|[^a-z ]')
    text = clean_patterns.sub(' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def _normalize_whitespace(text):
    corrected = re.sub(r'\s+', ' ', text)
    return corrected.strip()

def clean_stopwords(text):
    stopword = set(stopwords.words('indonesian'))
    text = ' '.join(word for word in text.split() if word not in stopword)
    return text.strip()

def sastrawistemmer(text):
    factory = StemmerFactory()
    st = factory.create_stemmer()
    return ' '.join(st.stem(word) for word in tqdm(text.split()) if word in text)

# Streamlit User Interface
def main():
    st.title("Prediksi Kategori Berita Online")
    st.write("Masukan Link Berita dari website MetroTVnews.")

    url_input = st.text_input("Masukkan Link Berita", "")
    if st.button("Prediksi"):
        if url_input:
            driver = web_driver()
            article_data = extract_article_content(driver, url_input)
            driver.quit()

            if article_data['Content']:
                df = pd.DataFrame([article_data])

                # Proses pembersihan teks
                df['lower case'] = df['Content'].apply(clean_lower)
                df['tanda baca'] = df['lower case'].apply(clean_punct)
                df['spasi'] = df['tanda baca'].apply(_normalize_whitespace)
                df['stopwords'] = df['spasi'].apply(clean_stopwords)
                df['stemming'] = df['stopwords'].apply(sastrawistemmer)

                # Membuat VSM
                filename_vectorizer = 'tfidf_vectorizer.sav'
                tfidf_vectorizer = pickle.load(open(filename_vectorizer, 'rb'))
                corpus = df['stemming'].tolist()
                x_tfidf = tfidf_vectorizer.transform(corpus)
                feature_names = tfidf_vectorizer.get_feature_names_out()
                tfidf_df = pd.DataFrame(x_tfidf.toarray(), columns=feature_names)
                cat_df = df["Category"]
                tfidf_df['Category'] = cat_df.values

                # Encode label kategori
                label_encoder = preprocessing.LabelEncoder()
                tfidf_df['Category'] = label_encoder.fit_transform(tfidf_df['Category'])

                # Load model dan prediksi
                filename_model = 'lr_model.sav'
                lr_model = pickle.load(open(filename_model, 'rb'))

                y_pred = lr_model.predict(tfidf_df.drop(['Category'], axis=1))
                category_map = {0: 'ekonomi', 1: 'internasional', 2: 'nasional', 3: 'olahraga', 4: 'peristiwa'}
                y_pred_labels = [category_map[pred] for pred in y_pred]

                st.write(f"Hasil prediksi kategori berita: **{y_pred_labels[0]}**")
            else:
                st.write("Konten berita tidak dapat diambil. Pastikan link yang dimasukkan benar.")
        else:
            st.write("Silakan masukkan Link beritanya dulu.")

if __name__ == "__main__":
    st.set_page_config(page_title="News Classification", page_icon="📰")
    main()
