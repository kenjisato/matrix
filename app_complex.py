import io

import numpy as np
import numpy.linalg as LA
import matplotlib.pyplot as plt
from shiny import module, render, ui, reactive, req, App

from util import ui_card_header, ui_katex

## 
## 複素固有値のケース
##

##------------------------
## UI
##------------------------


@module.ui
def panel(title):

    ui_input_eigenspace = ui.layout_columns(
        ui.card(
            ui_card_header("固有値"),
            ui.tags.div(
                ui.tags.div(
                    ui.input_numeric("s1", "実部", 0.5, step=0.05),
                    style="float: left; width: 45%;"
                ),
                ui.tags.div(
                    ui.input_numeric("s2", "虚部", 0.5, step=0.05),
                    style="float: right; width: 45%;"
                ),


                ui.tags.div(style="clear: both;"),

                ui.tooltip(
                    ui.tags.div(
                        ui.p("絶対値"),
                        ui.output_text_verbatim("abs_"),
                    ),
                    "原点を起点としたときの拡大・縮小の比率を表す。"
                ),
                
                ui.tooltip(
                    ui.tags.div(
                        ui.p("偏角 (度)"),
                        ui.output_text_verbatim("angle"),
                    ),
                    "橙から青の向きに回転する大きさに対応する。偏角＝45度のとき、橙軸上から青軸に動くまで2ステップで届く。"
                ),
            ),      
        ),
        ui.card(
            ui_card_header("固有ベクトル"), 
            ui.card_body(
                ui.tooltip(
                    ui.tags.div(
                        ui.h5("第1成分"),
                        ui.tags.div(
                            ui.input_numeric("a1", "実部 (青x)", 1.0, step=0.05),
                            style="float: left; width: 45%;"
                        ),
                        ui.tags.div(
                            ui.input_numeric("b1", "虚部 (橙x)", 0.2, step=0.05),
                            style="float: right; width: 45%;"
                        ),
                        ui.tags.div(
                            ui.h5("第2成分"),
                            ui.tags.div(
                                ui.input_numeric("a2", "実部 (青y)", 0.1, step=0.05),
                                style="float: left; width: 45%;"
                            ),
                            ui.tags.div(
                                ui.input_numeric("b2", "虚部 (橙y)", 0.8, step=0.05),
                                style="float: right; width: 45%;"
                            ),
                        ),
                    ),
                    r"$Av = \lambda v$ となる固有ベクトル $v$ を実部と虚部に分解する $v = \alpha + \beta j$。このとき、実部のベクトル $\alpha$ が青軸に対応、虚部のベクトル $\beta$ が橙軸に対応する。"
                ),

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
                ui.download_link("btn_download", "Save Figure")
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
        
        a1 = input["a1"]()
        a2 = input["a2"]()
        b1 = input["b1"]()
        b2 = input["b2"]()
        return np.array(
            [[a1 + b1 * 1j, a1 - b1 * 1j], 
             [a2 + b2 * 1j, a2 - b2 * 1j]
        ])
    
    @reactive.calc
    def R():
        
        a1 = input["a1"]()
        a2 = input["a2"]()
        b1 = input["b1"]()
        b2 = input["b2"]()
        return np.array(
            [[a1, b1], 
             [a2, b2]
        ])

    @reactive.calc
    def E():
        s1 = input["s1"]()
        s2 = input["s2"]()
        return np.array([s1 + s2 * 1j, s1 - s2 * 1j])
    
    @render.text
    def angle():
        return np.angle(input.s1() + input.s2() * 1j) * 180 / np.pi
    
    @render.text
    def abs_():
        return abs(input.s1() + input.s2() * 1j)

    @reactive.calc
    def A():
        try:
            A_ = (V() @ np.diag(E()) @ LA.inv(V())).real
        except:
            A_ = None
        return A_

    @render.ui
    def show_matrix():
        req(A)

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
        req(A)

        traj = trajectory()

        last_coord = traj[-1]

        try:
            new_coord = A() @ np.array(last_coord)
            traj.append(new_coord)
            trajectory.set(traj)
        except:
            ui.modal_show(
                ui.modal(ui.markdown("""
                        ### 固有ベクトルの設定エラー
                        
                        青軸と橙軸が平行です！ 
                        """))
            )


    @render.download(filename="plot.png")
    def btn_download():
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
            x = grid * R()[0, d]
            y = grid * R()[1, d]
            ax.plot(x, y, color=color[d], alpha=0.8)

        for d in [0, 1]:
            ax.arrow(0, 0, R()[0, d], R()[1, d], color=color[d],
                     width=0.1)

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
    panel("app", "複素固有値のケース"),
    title="Dynamics of 2x2 Matrix",
    id="page",
)

def server(input, output, session):
    app_server("app")

app = App(app_ui, server, debug=False)
