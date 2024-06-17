from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from datetime import datetime
import json
import time
import urllib.parse

# 현재 날짜 가져오기
current_date = datetime.now().strftime("%Y-%m-%d")
filename = f"MusicalData/pychart_M_total{current_date}.json"

# 웹 드라이버 설정
options = ChromeOptions()
options.add_argument("--disable-dev-shm-usage")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
options.add_argument("--headless")  # Headless 모드 추가
options.add_argument("--no-sandbox")  # GitHub Actions에서 필요한 설정
options.add_argument("--disable-gpu")  # GitHub Actions에서 필요한 설정
options.add_argument("--window-size=1920,1080")  # Headless 모드에서 창 크기 설정
service = ChromeService(ChromeDriverManager().install())
browser = webdriver.Chrome(service=service, options=options)

def get_melon_ranking():
    # 멜론 사이트에서 순위 데이터를 가져오기
    url = "https://ticket.melon.com/ranking/index.htm"
    browser.get(url)
    time.sleep(5)  # 페이지 로딩 대기

    # "뮤지컬/연극" 버튼 클릭
    concert_button = WebDriverWait(browser, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[@value='NEW_GENRE_ART']"))
    )
    concert_button.click()
    print("Clicked '뮤지컬/연극' button.")
    time.sleep(5)  # 페이지가 완전히 로드될 때까지 대기

    # 전체 순위 데이터 가져오기
    page_source = WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".tbl.tbl_style02 tbody"))
    ).get_attribute('innerHTML')
    soup = BeautifulSoup(page_source, 'html.parser')
    tracks = soup.select("tr")

    return tracks

def get_cast_info(title):
    try:
        query = urllib.parse.quote(title + " 출연진")
        search_url = f"https://search.naver.com/search.naver?where=nexearch&sm=tab_etc&mra=bkkw&pkid=269&query={query}"
        browser.get(search_url)
        time.sleep(5)  # 페이지 로딩 대기

        # 검색 결과 페이지가 로드되었는지 확인
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".list_image_info"))
        )
        print(f"Loaded cast list for {title}.")

        # 페이지 소스 가져오기
        page_source = browser.page_source

        # BeautifulSoup을 사용하여 HTML 파싱
        soup = BeautifulSoup(page_source, 'html.parser')

        # 출연진 데이터 추출
        cast_data = []
        cast_items = soup.select(".list_image_info ._item")
        if not cast_items:
            print(f"No cast items found for {title}.")
            return "정보없음"

        for item in cast_items:
            img_url = item.select_one("div.thumb img").get('src') if item.select_one("div.thumb img") else "정보없음"
            name = item.select_one("div.title_box strong.name.type_ell_1").text.strip() if item.select_one("div.title_box strong.name.type_ell_1") else "정보없음"
            role = item.select_one("div.title_box span.sub_text.type_ell_2").text.strip() if item.select_one("div.title_box span.sub_text.type_ell_2") else "정보없음"

            cast_data.append({
                "img_url": img_url,
                "name": name,
                "role": role
            })

        return cast_data

    except Exception as e:
        print(f"Error processing {title}:", e)
        return "정보없음"

def get_casting_info(title):
    try:
        query = urllib.parse.quote(title + " 캐스팅일정")
        search_url = f"https://search.naver.com/search.naver?where=nexearch&sm=tab_etc&mra=bkkw&pkid=269&query={query}"
        browser.get(search_url)
        time.sleep(10)  # 페이지 로딩 대기

        # 검색 결과 페이지가 로드되었는지 확인
        WebDriverWait(browser, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".timeline_list.casting_list"))
        )
        print(f"Loaded casting schedule for {title}.")

        # 페이지 소스 가져오기
        page_source = browser.page_source

        # BeautifulSoup을 사용하여 HTML 파싱
        soup = BeautifulSoup(page_source, 'html.parser')

        # 캐스팅 일정 데이터 추출
        casting_data = []
        casting_items = soup.select(".timeline_list.casting_list li")
        if not casting_items:
            print(f"No casting items found for {title}.")
            return "정보없음"

        for item in casting_items:
            cast_date = item.select_one(".cm_date").text.strip() if item.select_one(".cm_date") else "정보없음"
            time_contents = item.select(".time_content")
            for time_content in time_contents:
                cast_time = time_content.select_one(".time_title time").text.strip() if time_content.select_one(".time_title time") else "정보없음"
                cast_list = []
                cast_items = time_content.select(".list .area_link")
                for cast in cast_items:
                    name = cast.select_one(".name").text.strip() if cast.select_one(".name") else "정보없음"
                    role = cast.select_one(".sub_text").text.strip() if cast.select_one(".sub_text") else "정보없음"
                    cast_list.append({"name": name, "role": role})

                casting_data.append({
                    "cast_date": cast_date,
                    "cast_time": cast_time,
                    "cast_list": cast_list
                })

        return casting_data

    except Exception as e:
        print(f"Error processing {title}:", e)
        return "정보없음"

# 멜론 순위 데이터를 가져와서 처리
try:
    tracks = get_melon_ranking()
    music_data = []

    for track in tracks:
        rank = track.select_one("td.fst .ranking").text.strip() if track.select_one("td.fst .ranking") else "정보없음"
        change = track.select_one("td.fst .change").text.strip() if track.select_one("td.fst .change") else "정보없음"
        # change 텍스트에서 불필요한 공백 제거
        change = ' '.join(change.split()) if change != "정보없음" else "정보없음"
        title = track.select_one("div.show_infor p.infor_text a").text.strip() if track.select_one("div.show_infor p.infor_text a") else "정보없음"
        place = track.select_one("td:nth-child(4)").text.strip() if track.select_one("td:nth-child(4)") else "정보없음"
        image_url = track.select_one("div.thumb_90x125 img").get('src') if track.select_one("div.thumb_90x125 img") else "정보없음"
        site_url = "https://ticket.melon.com/ranking/index.htm"
        date_elements = track.select("ul.show_date li")
        date = " ".join([element.text.strip() for element in date_elements]) if date_elements else "정보없음"

        music_entry = {
            "rank": rank,
            "change": change,
            "title": title,
            "Venue": place,
            "ImageURL": image_url,
            "site": site_url,
            "date": date
        }

        # 네이버에서 출연진 및 캐스팅 일정 데이터 추가
        music_entry['cast'] = get_cast_info(title)
        music_entry['casting_schedule'] = get_casting_info(title)
        music_data.append(music_entry)

    # 데이터를 JSON 파일로 저장
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(music_data, f, ensure_ascii=False, indent=4)

    print("All ranking data saved to JSON file.")

except Exception as e:
    print("Error processing the Melon ranking data:", e)

# 브라우저 종료
browser.quit()
