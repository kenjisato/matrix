import app_real
import app_complex

from shiny import App, ui

from util import ui_katex

app_ui = ui.page_navbar(
    ui.head_content(ui.include_css("css/custom.css")),
    ui_katex,
    app_real.panel("real", "実固有値のケース"),
    app_complex.panel("comp", "複素固有値のケース"),
    ui.nav_control(),
    title="Dynamics of 2x2 Matrix",
    id="page",
)

def server(input, output, session):
    app_real.app_server("real")
    app_complex.app_server("comp")

# shiny app ----
app = App(app_ui, server, debug=False)
