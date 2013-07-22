from flask import render_template


def index():
    return render_template('projects.html', projects=True)
