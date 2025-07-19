from dash import html
import dash_ag_grid as dag
from services.db import get_connection

def get_filtered_df():
    conn = get_connection()
    df = conn.execute("SELECT * FROM Invoice").fetchdf()
    return df

def layout():
    df = get_filtered_df()

    return html.Div([
        html.H4("Filtered Invoice Table"),
        dag.AgGrid(
            id="table-overview",
            columnDefs=[{"field": col, "sortable": True, "filter": True} for col in df.columns],
            rowData=df.to_dict("records"),
            style={"height": "600px", "width": "100%"}
        )
    ])
