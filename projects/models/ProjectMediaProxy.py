from .Projects import Projects

class ProjectMediaProxy(Projects):
    

    class Meta:
        verbose_name = "Project Gallery"              # singular name in sidebar and forms
        verbose_name_plural = "Projects Gallery"
        proxy = True




