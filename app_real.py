import io

import numpy as np
import numpy.linalg as LA
import matplotlib.pyplot as plt
from shiny import module, render, ui, reactive, req, App

from util import ui_card_header, ui_katex

## 
## 実固有値のケース
##

##------------------------
## UI
##------------------------

@module.ui
def panel(title):

    ui_input_eigenspace = ui.layout_columns(
        ui.card(
            ui_card_header("固有空間 1 (青)"), 
            ui.card_body(
                ui.input_numeric("s1", "固有値1", 0.9, step=0.05),
                ui.input_numeric("11", "固有ベクトル1", 1.0, step=0.05),
                ui.input_numeric("21", "", 0.2, step=0.05),
            ),
        ),
        ui.card(
            ui_card_header("固有空間 2 (オレンジ)"), 
            ui.card_body(
                ui.input_numeric("s2", "固有値2", -0.95, step=0.05),
                ui.input_numeric("12", "固有ベクトル2", 0.45, step=0.05),
                ui.input_numeric("22", "", 1.0, step=0.05),
            ),
        ),
        col_widths=(6, 6),
    )

    ui_simulation_params = ui.layout_columns(
        ui.card(
            ui_card_header("行列 A"),
            ui.TagList(
                ui.p(r"$\begin{bmatrix} x_{t+1}\\ y_{t+1}\end{bmatrix} = A \begin{bmatrix} x_{t}\\ y_{t}\end{bmatrix}$"),
                ui.output_ui("show_matrix"),
            ),
        ),
        ui.card(
            ui_card_header("初期値"),
            ui.input_numeric("x0", "$x_0$", 9.0),
            ui.input_numeric("y0", "$y_0$", 7.0),
        ),
        col_widths=(6, 6), 
    )


    _ui = ui.layout_sidebar(
        ui.sidebar(
            ui_input_eigenspace, 
            ui_simulation_params,
            width='500px',
        ),
        ui.navset_tab(
            ui.nav_panel(
                "相図",
                ui.card(
                    ui.card_body(
                        ui.output_plot("plot_simulation"),
                    ),
                    full_screen=True,
                ),
                value="ps"
            ),
            ui.nav_panel(
                "時系列",
                ui.card(
                    ui.card_body(
                        ui.output_plot("plot_timeseries"),
                    ),
                    full_screen=True,
                ),
                value="ts",
            ),
            ui.nav_spacer(),
            ui.nav_control(
                ui.download_link("btn_download_real", "Save Figure")
            ),
            id="app_nav",
        ),
        ui.input_action_button("btn_next", "Next"),
    )

    return ui.nav_panel(title, _ui)


##------------------------
## Server
##------------------------

color = ['C0', 'C1', 'C2']

@module.server
def app_server(input, output, session):

    @reactive.calc
    def V():
        
        v11 = input["11"]()
        v12 = input["12"]()
        v21 = input["21"]()
        v22 = input["22"]()
        return np.array([[v11, v12], [v21, v22]])

    @reactive.calc
    def E():
        s1 = input["s1"]()
        s2 = input["s2"]()
        return np.array([s1, s2])

    @reactive.calc
    def A():
        try:
            A_ = V() @ np.diag(E()) @ LA.inv(V())
        except:
            A_ = None
        return A_

    @render.ui
    def show_matrix():
        return ui.tags.table(
            ui.TagList(
                ui.tags.tr(
                    ui.tags.td(str(round(A()[0, 0], 3))),
                    ui.tags.td(str(round(A()[0, 1], 3)))
                ),
                ui.tags.tr(
                    ui.tags.td(str(round(A()[1, 0], 3))),
                    ui.tags.td(str(round(A()[1, 1], 3)))
                ),
            ), 
            class_="matrix-table",
        )

    trajectory = reactive.value([])
    fig_ps = reactive.value()
    fig_ts = reactive.value()

    @reactive.effect
    @reactive.event(A, input.x0, input.y0)
    def reset():
        coord = (input.x0(), input.y0())
        trajectory.set([coord])

    @reactive.effect
    @reactive.event(input.btn_next)
    def update_trajectory():
        traj = trajectory()

        last_coord = traj[-1]
        new_coord = A() @ np.array(last_coord)
        traj.append(new_coord)
        trajectory.set(traj)


    @render.download(filename="plot.png")
    def btn_download_real():
        if input.app_nav() == "ps":
            figure = fig_ps()
        else:
            figure = fig_ts()

        with io.BytesIO() as buf:
            figure.savefig(buf, format="png", bbox_inches="tight")
            yield buf.getvalue()


    @render.plot
    @reactive.event(input.btn_next, trajectory)
    def plot_simulation():
        req(A)

        traj = trajectory()

        figure, ax = plt.subplots()
        grid = np.linspace(-100, 100, 200)

        ax.set_aspect(1)
        ax.set_xlim((-10, 10))
        ax.set_ylim((-10, 10))
        ax.set_xlabel('x')
        ax.set_ylabel('y')
        
        for d in [0, 1]:
            x = grid * V()[0, d]
            y = grid * V()[1, d]
            ax.plot(x, y, color=color[d], alpha=0.8)

        for circ in traj:
            point = plt.Circle((circ[0], circ[1]), 0.2, color=color[2], alpha=0.4, zorder=10)
            ax.add_artist(point)

        fig_ps.set(figure)
        return figure
    

    def tmax(t, chunk_size=20):  
        n = t // chunk_size + 1
        return n * chunk_size

    @render.plot
    @reactive.event(input.btn_next, trajectory)
    def plot_timeseries():
        req(A)

        traj = trajectory()

        T = len(traj)

        x, y = np.empty(T), np.empty(T)

        for i, xy in enumerate(traj):
            x[i] = xy[0]
            y[i] = xy[1]

        figure, ax = plt.subplots(2, 1)

        ax[0].plot(x)
        ax[0].set_ylabel('x')
        ax[0].set_xlim(0, tmax(T))

        ax[1].plot(y)
        ax[1].set_ylabel('y')
        ax[1].set_xlim(0, tmax(T))

        fig_ts.set(figure)
        return figure
    

# shiny app ----

app_ui = ui.page_navbar(
    ui.head_content(ui.include_css("css/custom.css")),
    ui_katex,
    panel("app", "実固有値のケース"),
    title="Dynamics of 2x2 Matrix",
    id="page",
)

def server(input, output, session):
    app_server("app")

app = App(app_ui, server, debug=False)
