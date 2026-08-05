from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(['GET'])
@permission_classes([AllowAny])
def health(request):
    """Trivial reachability check for mobile/web clients - no auth required."""
    return Response({'status': 'ok'})
