import streamlit as st
from openai import OpenAI
import requests
from docx import Document
from docx.shared import Pt
from io import BytesIO
import base64

# OpenAI API 키 가져오기
api_key = st.secrets["OPENAI_API_KEY"]

# OpenAI API 클라이언트 초기화
client = OpenAI(api_key=api_key)

# GitHub 리포지토리 정보
GITHUB_REPO = "shlee2222/press"
GITHUB_FILE_PATH = "template.docx"

# 기본 글씨체 설정
DEFAULT_FONT = "맑은 고딕"
DEFAULT_FONT_SIZE = 15

# 보도자료 유형과 입력 데이터 정의
press_release_types = {
    "활동보고": {
        "활동내용": "예시) 평택시 창의채움교육센터 운영위원회 개최",
        "활동경과": "예시) 기존 위원 임기 만료에 따른 신규위원 위촉장 수여, 평택미래교육협력지구 사업 현황 공유",
        "향후계획": "예시) 인재양성을 위한 교육지원 사업 추진",
    },
    "성과보고": {
        "성과개요": "예시) 정장선 평택시장, 2024년 메니페스토 공약 이행 평가 '최우수(SA) 등급' 획득, 9대 분야 222개 공약, 2023년 목표 달성률 95.5%",
        "우리시 입장, 당부사항": "예시) 시민 참여 및 소통 강조, 투명한 공약 실천 지속",
        "향후계획": "예시) 시민 중심 새로운 평택 구현, 민선 8기 공약 이행률 향상 목표"
    },
    "행사안내": {
        "행사개요": "예시) 평택시 내리문화공원에서 7월 22일(토)부터 23일(일)까지 수국 전시회 개최.",
        "세부내용": "예시) 수국 관람 외 자연물 만들기 체험행사, 음악행사, 내리물놀이터 개장 및 그늘막 설치.",
        "참여방법": "예시) 가족 단위로 내리문화공원 방문, 체험행사는 매일 13시~17시 시간대별 운영.",
    },
    "정보안내": {
        "정보개요": "예시) 평택시도서관, 7월부터 책이음 상호대차 서비스 확대 운영.",
        "세부내용": "예시) 평택시 14개 도서관에서 경기평택교육도서관 포함 15개 도서관으로 서비스 확대.",
        "이용방법": "예시) 이용 문의는 도서관 누리집(www.ptlib.go.kr) 및 해당 도서관들로 가능.",
    },
    "기타":{
        "개요":"",
        "필수 키워드1": "",
        "필수 키워드2": ""
    }
}

def generate_press_release(release_type, inputs):
    prompt = f"보도자료 유형: {release_type}\n\n"
    for label, content in zip(press_release_types[release_type], inputs):
        prompt += f"{label}: {content}\n"
    prompt += "\n위의 정보를 바탕으로 전문적이고 공식적인 보도자료를 작성해주세요."

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "당신은 전문적인 보도자료 작성자입니다. 어조는 '~했습니다'가 아니라 '~했다'로 작성해주세요."},
            {"role": "system", "content": "보도자료의 구성은 제목, 서브타이틀, 본문 3개입니다. 파싱을 위해서 '제목:', '서브타이틀:', '본문:'이라고 표기해 주세요."},
            {"role": "assistant", "content": "아래 프롬프트문과 유사한 보도자료들을 검색해서 보도자료 내용을 강화해주세요"},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content.strip()

def download_github_file(repo, file_path):
    url = f"https://raw.githubusercontent.com/{repo}/main/{file_path}"
    response = requests.get(url)
    if response.status_code == 200:
        return BytesIO(response.content)
    else:
        st.error(f"GitHub에서 파일을 다운로드하는 데 실패했습니다. 상태 코드: {response.status_code}")
        return None

def insert_content_to_docx(template_file, content):
    doc = Document(template_file)
    paragraph = doc.add_paragraph(content)
    for run in paragraph.runs:
        run.font.name = DEFAULT_FONT
        run.font.size = Pt(DEFAULT_FONT_SIZE)
    return doc

def get_binary_file_downloader_html(bin_file, file_label='File'):
    bin_str = base64.b64encode(bin_file).decode()
    href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{file_label}">다운로드 {file_label}</a>'
    return href

def main():
    st.title("보도자료 생성기")

    # 보도자료 유형 선택
    release_type = st.radio("보도자료 유형을 선택하세요:", options=list(press_release_types.keys()), horizontal=True)

    if release_type:
        st.write(f"선택된 유형: {release_type}")

        # 입력 필드 생성
        inputs = {}
        for label, default_value in press_release_types[release_type].items():
            input_value = st.text_area(f"{label}:", value=default_value, height=100)
            inputs[label] = input_value

        if st.button("보도자료 생성"):
            filled_inputs = {k: v for k, v in inputs.items() if v.strip()}
            
            if filled_inputs:
                with st.spinner("보도자료를 생성 중입니다..."):
                    press_release = generate_press_release(release_type, filled_inputs.values())
                
                st.subheader("생성된 보도자료")
                st.write(press_release)

                # GitHub에서 템플릿 다운로드
                template_file = download_github_file(GITHUB_REPO, GITHUB_FILE_PATH)
                
                if template_file:
                    # 템플릿에 내용 삽입
                    doc = insert_content_to_docx(template_file, press_release)
                    
                    # 문서를 바이트로 변환
                    bio = BytesIO()
                    doc.save(bio)
                    bio.seek(0)
                    
                    # 다운로드 링크 생성
                    st.markdown(get_binary_file_downloader_html(bio.getvalue(), 'generated_press_release.docx'), unsafe_allow_html=True)
                else:
                    st.error("템플릿 파일을 다운로드할 수 없습니다. GitHub 리포지토리 설정을 확인해주세요.")
            else:
                st.warning("최소한 하나의 필드는 입력해주세요.")
    else:
        st.info("보도자료 유형을 선택해주세요.")

if __name__ == "__main__":
    main()
