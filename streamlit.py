import streamlit as st
from streamlit_searchbox import st_searchbox
import requests
import pandas as pd

st.set_page_config(
    page_title="Nahoď knihu",
    page_icon="📊",
    layout="wide",
    #initial_sidebar_state="expanded")
)


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
    print(book_ids)
    call = f"https://nahod-knihu-0fe888ecfa27.herokuapp.com/recommend-books/{book_ids}?thres_rating={slider_minRatings}"
    if cbox_authors:
        call += "&exclude_authors"
    if cbox_genres:
        call += "&keep_genres"
    res = requests.get(call)
    print(res.json())
    print(pd.DataFrame.from_dict(res.json(),orient="index"))
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
    st.session_state.data = pd.DataFrame(columns=["id","title","authors","rating"])

if "results" not in st.session_state:
    st.session_state.results = pd.DataFrame()

if "lastShown" not in st.session_state:
    st.session_state.lastShown = -1

st.sidebar.title("Nahoď knihu!")
st.sidebar.subheader("Váš AI knihovník")

# pass search function to searchbox
st.session_state.selected_value = st_searchbox(
    search_database,
    placeholder = "Název knihy nebo její část",
    default = None,
    label = "Zadej knihy, které sis v poslední době užil:",
    key="book_searchbox",
    clear_on_submit = True,
)

if st.session_state.selected_value:
    if st.session_state.selected_value not in st.session_state.selected_books:
        st.session_state.selected_books.append(st.session_state.selected_value)
        book_info = get_book_info(st.session_state.selected_value)
        st.session_state.data.loc[len(st.session_state.data)] = [st.session_state.selected_value,book_info["title"],book_info["authors"],book_info["rating"]]
        st.session_state.selected_value = None

st.dataframe(st.session_state.data[["title","authors","rating"]],hide_index=True,width=1200,key="df_selected_books",on_select=callback)

#cbox_authors = st.checkbox("Vynechat původní autory")


col1, col2, col3 = st.columns(3)
cbox_authors = col1.checkbox("Vynechat původní autory",key="cbox_authors")
cbox_genres = col2.checkbox("Stejné žánry",key="cbox_genres")
slider_minRatings = col3.slider("Minimální hodnocení",0,100)

#cbox_genres = st.checkbox("Stejné žánry")
#slider_minRatings = st.slider("Minimální hodnocení",0,100)

st.button("Hledat podobné knihy",on_click=get_results)

column_config={
        "title": "Název knihy",
        "authors": "Autoři",
        "candidates": "Podobnost",
        "genres": "Žánry",
        "rating": st.column_config.NumberColumn(
            "Hodnocení",
            format="%d ⭐"
        ),
        "url": st.column_config.LinkColumn("Odkaz databáze knih",display_text="Databáze knih"),
    }

if len(st.session_state.results) > 0:
    st.dataframe(st.session_state.results[["title","authors","rating","candidates","genres","url"]].sort_values("candidates",ascending=False),width=1200,column_config = column_config,hide_index=True,selection_mode="single-row",on_select=show_book, key="info_book")
    #st.dataframe(st.session_state.results,hide_index=True,width=800)
