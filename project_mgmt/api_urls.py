from rest_framework.routers import DefaultRouter
from .api_views import ProjectViewSet, TaskViewSet, TimeEntryViewSet, ProjectReportViewSet

router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'timeentries', TimeEntryViewSet, basename='timeentry')
router.register(r'projectreports', ProjectReportViewSet, basename='projectreport')

urlpatterns = router.urls 