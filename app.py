from datetime import date, datetime, time, timedelta 
import numpy as np
import requests
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st
import plotly.express as px
from PIL import Image
from src import agstyler, db
from src.agstyler import PRECISION_ZERO

# Update NumPy objects  

np.bool = np.bool_
np.object = np.object_

# Add page headings

st.set_page_config(page_title="Wettbewerb Klimaschutz-nebenan")
st.markdown('<style>div.block-container{padding-top:1rem;}</style>', unsafe_allow_html=True) # Reduce spacing to the top
st.header("Wettbewerb Klimaschutz-nebenan")
st.subheader("Zwischenergebnisse")

# Scrape data from web

link = "https://www.klimaschutz-nebenan.de/ideen/2023"
response = requests.get(link)
page = BeautifulSoup(response.content, "html.parser")
data = [elem.get_text() for elem in page.select(".justify-center")]

# Prepare data

id = range(1, len(data) + 1)
df = pd.DataFrame({"id": id, "data": data})
name = df[df["id"] % 2 == 0].reset_index().drop(["id", "index"], axis=1)
points = df[df["id"] % 2 == 1].reset_index().drop(["id", "index"], axis=1)
result = pd.concat([name, points], axis=1)
result.columns = ["Projekt", "Punkte"]
result = result.replace(r'\n','', regex=True).iloc[:100]
result["Punkte"] = result["Punkte"].astype(int)
result = result.sort_values(by="Punkte", ascending=False).reset_index(drop=True)
result.index = result.index + 1
result["Platz"] = result.index

# Determine index and votes of specific project

search = "Stadt selbst gestalten - weniger grau, mehr grün"
rank = result[result["Projekt"] == search]["Punkte"].index[0]
points_search = result[result["Projekt"] == search]["Punkte"].values[0]
st.markdown(f'**Projekt "_{search}_"**')
st.markdown(f'{points_search} Punkte (Platz {rank})')

# Show data as formatted dataframe and highlight the specific project

formatter_rows = {
    'Platz': ('Platz', {'width': 62}),    
    'Projekt': ('Projekt', {'width': 500}),
    'Punkte': ('Punkte', {**PRECISION_ZERO, 'width': 72})
}
go = {
    'rowClassRules': 
        {'project': f'data.Projekt == "{search}"'}
}
css = {
    '.project': 
        {'background-color': 'green'}
}
agstyler.draw_grid(
    result, formatter_rows, grid_options=go, css=css, fit_columns=True, max_height=455
)

# Remaining time part

now = datetime.now()
resttime = datetime.fromisoformat("2023-08-25T23:59:59") - now # Remaining time for online voting

days = resttime.days                            # Days...
hours = int(resttime.seconds/3600)              # Hours...
minutes = int(resttime.seconds % 3600 / 60)     # Minutes...
seconds = int(resttime.seconds % 60)            # Seconds until online voting will end

# Text output showing the remaining time for online voting

link='[klimaschutz-nebenan](https://www.klimaschutz-nebenan.de/idee/2023/stadt-selbst-gestalten-weniger-grau-mehr-grun)!'
if days == 1:
    days_string = "Tag"
else:
    days_string = "Tage"
if hours == 1:
    hours_string = "Stunde"
else:
    hours_string = "Stunden"
if minutes == 1:
    minutes_string = "Minute"
else:
    minutes_string = "Minuten"
st.markdown(f'Jetzt noch {days} {days_string}, {hours} {hours_string}, {minutes} {minutes_string} abstimmen unter {link}', unsafe_allow_html=True)


# Comments part

COMMENT_TEMPLATE_MD = """{} - {}
> {}"""

conn = db.connect()
comments = db.collect(conn)

with st.expander("💬 Kommentare anzeigen"):

    # Show comments

    st.write("**Kommentare:**")

    for index, entry in enumerate(comments.itertuples()):
        st.markdown(COMMENT_TEMPLATE_MD.format(entry.name, entry.date, entry.comment))

        is_last = index == len(comments) - 1
        is_new = "just_posted" in st.session_state and is_last
        if is_new:
            st.success("☝️ Ihr Wunsch wurde erfolgreich hinzugefügt.")

    # Insert comment

    st.write("**Was ist Deine Idee, um die Fläche um die Velobox herum zu verschönern :**")
    form = st.form("comment")
    name = form.text_input("Name")
    comment = form.text_area("Meine Idee")
    submit = form.form_submit_button("Idee hinzufügen")

    if submit:
        date = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        db.insert(conn, [[name, comment, date]])
        if "just_posted" not in st.session_state:
            st.session_state["just_posted"] = True
        st.experimental_rerun()
