import dash

import view
import callbacks


#app = dash.Dash(__name__, external_stylesheets=["https://codepen.io/chriddyp/pen/bWLwgP.css"])
app = dash.Dash(__name__)

app.layout = view.create_layout()

callbacks.register_callbacks(app)

if __name__ == '__main__':
    app.run_server(debug=True)
