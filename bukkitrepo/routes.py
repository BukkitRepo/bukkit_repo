from bukkitrepo import app


# Import views
import bukkitrepo.views.projects


# Projects routes
app.add_url_rule('/', 'root_url', bukkitrepo.views.projects.index)
app.add_url_rule('/projects/', 'projects_index', bukkitrepo.views.projects.index)
