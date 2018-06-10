import dash

app = dash.Dash()
server = app.server
app.config.suppress_callback_exceptions = True

# Bootstrap sample template for css
css_source = ['https://stackpath.bootstrapcdn.com/bootstrap/4.1.1/css/bootstrap.min.css','https://codepen.io/bricakeld/pen/qKZeGq.css']
for css in css_source:
    app.css.append_css({'external_url': css})
