import streamlit as st
from streamlit_searchbox import st_searchbox
import requests
import pandas as pd
import os

st.set_page_config(
    page_title="Nahoď knihu",
    page_icon="📊",
    layout="wide",
    #initial_sidebar_state="expanded")
)

if "OPENAI_API_KEY" in os.environ.keys():
    pass
    #print(os.environ['OPENAI_API_KEY'])
elif "OPENAI_API_KEY" in st.secrets.keys():
    os.environ["OPENAI_API_KEY"] = st.secrets["OPEN_API_KEY"]

def search_database(searchterm: str) -> list[any]:
    if searchterm:
        res = requests.get(f"https://nahod-knihu-0fe888ecfa27.herokuapp.com/get-books/{searchterm}")
        #print(res.json())
        return [(value["title"],key) for key,value in res.json().items()]
    else:
        []

def get_book_info(id: int) -> dict[str, any]:
    res = requests.get(f"https://nahod-knihu-0fe888ecfa27.herokuapp.com/get-book/{id}")
    #print(res.json())
    return res.json()

def get_results() -> any:
    if len(st.session_state.data) == 0:
        st.warning('Musíte vybrat nějakou Vaši oblíbenou knihu!', icon="⚠️")
        return None
    book_ids = ",".join(st.session_state.data["id"].to_list())
    #print(book_ids)
    call = f"https://nahod-knihu-0fe888ecfa27.herokuapp.com/recommend-books/{book_ids}?thres_rating={slider_minRatings}&thres_year={slider_minYear}"
    if cbox_authors:
        call += "&exclude_authors"
    if cbox_genres:
        call += "&keep_genres"
    res = requests.get(call)
    #print(res.json())
    #print(pd.DataFrame.from_dict(res.json(),orient="index"))
    st.session_state.results = pd.DataFrame.from_dict(res.json(),orient="index")

def get_results_byText() -> any:
    if len(st.session_state.descText) < 20:
        st.warning('Musíte použít alespoň 20 znaků na popis knihy!', icon="⚠️")
        return None
    #call = f"http://127.0.0.1:8000/recommend-books-byText/{st.session_state.descText}?thres_rating={slider_minRatings}&thres_year={slider_minYear}"
    call = f"https://nahod-knihu-0fe888ecfa27.herokuapp.com//recommend-books-byText/{st.session_state.descText}?thres_rating={slider_minRatings}&thres_year={slider_minYear}"
    res = requests.get(call)
    st.session_state.results = pd.DataFrame.from_dict(res.json(),orient="index")

def callback():
    #print(st.session_state.df_selected_books)
    st.session_state["data"] = st.session_state["data"].drop(st.session_state.df_selected_books["selection"]["rows"],axis=0)
    #print(st.session_state["data"])

@st.dialog("Informace o vybrané knize")
def vote(item):
    #st.write(item)
    st.title(f"{item['title']} - {item['authors']}")
    st.write(f"Hodnocení: {item['rating']} %")
    st.write(f"Rok vydání: {item['publish_year']}")
    st.write(f"Žánry: {', '.join(item['genres'])}")
    st.write(item["description"])
    st.session_state.info_book["selection"]["rows"] = []
    st.link_button("Přejít na databázi knih", item["url"])
    st.session_state.lastShown = item.name

def show_book() -> None:
    book_to_show = st.session_state.results.sort_values("candidates",ascending=False).iloc[st.session_state.info_book["selection"]["rows"][0]]
    if len(st.session_state.info_book["selection"]["rows"]) != 0 and book_to_show.name != st.session_state.lastShown:
        #vote(st.session_state.results.sort_values("candidates",ascending=False).iloc[st.session_state.info_book["selection"]["rows"][0]])
        vote(book_to_show)

if "selected_books" not in st.session_state:
    st.session_state.selected_books = []

if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["id","title","authors","rating","publish_year"])

if "results" not in st.session_state:
    st.session_state.results = pd.DataFrame()

if "lastShown" not in st.session_state:
    st.session_state.lastShown = -1

if "descText" not in st.session_state:
    st.session_state.descText = ""

#st.logo("logo.png")
st.sidebar.title("Nahoď knihu!")
st.sidebar.subheader("Váš AI knihovník")
st.sidebar.write("Dočetli jsme někdy knihu a položili si otázku a jaká kniha bude další?")
st.sidebar.write("Jak vybíráte nové knihy? Doporučení od rodiny, přátel, na diskuzním fóru?")
st.sidebar.write("Máme pro Vás ještě jednu možnost!")
st.sidebar.write("Nechte si knihy doporučit od AI pomocí podobnosti popisků knih na obalu knihy.")
st.sidebar.write("Jednoduše zadáte pár podobných knih, které se Vám líbily ...")
st.sidebar.write("... a my Vám nabídneme další!")

st.sidebar.divider()

search_mode = st.sidebar.radio(
    "Jak chcete hledat nové knihy",
    ["***Podle jiných knih 📚***", "***Podle Vašeho popisu ✍***"],
    captions=[
        "Podle podobnosti s vybranými knihami.",
        "Podle podobnosti Vašeho textu s popisem knihy.",
    ],
)

if search_mode == "***Podle jiných knih 📚***":
# pass search function to searchbox
    st.session_state.selected_value = st_searchbox(
        search_database,
        placeholder = "Název knihy nebo jméno autora",
        default = None,
        label = "Zadej knihy, které sis v poslední době užil:",
        key="book_searchbox",
        clear_on_submit = True,
    )

    if st.session_state.selected_value:
        if st.session_state.selected_value not in st.session_state.selected_books:
            st.session_state.selected_books.append(st.session_state.selected_value)
            book_info = get_book_info(st.session_state.selected_value)
            st.session_state.data.loc[len(st.session_state.data)] = [st.session_state.selected_value,book_info["title"],book_info["authors"],book_info["rating"],book_info["publish_year"]]
            st.session_state.selected_value = None

    search_column_config={
        "title": "Název knihy",
        "authors": "Autoři",
        "rating": st.column_config.NumberColumn(
            "Hodnocení",
            format="%d ⭐",
            width="small"
        ),
        #"publish_year": "Rok vydání",
        "publish_year": st.column_config.TextColumn(
            "Rok vydání",
            #format="YYYY",
            width="small",
        ),
    }

    if len(st.session_state.data) > 0:
        st.dataframe(st.session_state.data[["title","authors","rating","publish_year"]],hide_index=True,width=1200,key="df_selected_books",on_select=callback,column_config=search_column_config)

else:
    st.session_state.descText = st.text_area("Nové knihy by měly být o:",placeholder="mladém chlapci, který jako dítě přežil pokus o vraždu a později zjistil, že jě kouzelníkem ...")



col1, col2, col3 = st.columns((1,2,2))
if search_mode == "***Podle jiných knih 📚***":
	cbox_authors = col1.checkbox("Vynechat původní autory",key="cbox_authors")
	cbox_genres = col1.checkbox("Stejné žánry",key="cbox_genres")
slider_minRatings = col2.slider("Minimální hodnocení",0,100,value=70)
slider_minYear = col3.slider("Minimální rok vydání",1900,2026, value=1970)

if search_mode == "***Podle jiných knih 📚***":
	st.button("Hledat podobné knihy",on_click=get_results)
else:
	st.button("Hledat popsané knihy",on_click=get_results_byText)


column_config={
        "title": "Název knihy",
        "authors": "Autoři",
        "candidates": "Podobnost",
        "publish_year": st.column_config.TextColumn(
            "Rok vydání",
        ),
        "genres": "Žánry",
        "rating": st.column_config.NumberColumn(
            "Hodnocení",
            format="%d ⭐"
        ),
        "url": st.column_config.LinkColumn("Odkazy",display_text="Databáze knih"),
    }

if len(st.session_state.results) > 0:
    st.dataframe(st.session_state.results[["title","authors","rating","publish_year","candidates","genres","url"]].sort_values("candidates",ascending=False),width=1200,column_config = column_config,hide_index=True,selection_mode="single-row",on_select=show_book, key="info_book")
    #st.dataframe(st.session_state.results,hide_index=True,width=800)

footer_html = """<div style='text-align: center;'>
  <p>Vyvinuto s ❤️  by Fajťák. Případné dotazy, přípomínky, stížnosti a nápady posílejte na nahodknihu@gmail.com</p>
</div>"""
st.markdown(footer_html, unsafe_allow_html=True)
