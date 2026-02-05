from app import app

from app.User import User
from app.Project import Project
from app.File import File
from app.Analysis import Analysis
from app.Graph import Graph
from app.ArchTag import ArchTag

app.register_blueprint(User, url_prefix="/User")
app.register_blueprint(Project, url_prefix="/Project")
app.register_blueprint(File, url_prefix="/File")
app.register_blueprint(Analysis, url_prefix="/Analysis")
app.register_blueprint(Graph, url_prefix="/Graph")
app.register_blueprint(ArchTag, url_prefix="/ArchTag")
