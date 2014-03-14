from sqlalchemy.orm import joinedload

from changes.api.base import APIView
from changes.models import Change


class ChangeDetailsAPIView(APIView):
    def get(self, change_id):
        change = Change.query.options(
            joinedload(Change.project),
            joinedload(Change.author),
        ).get(change_id)

        return self.respond(change)

    def get_stream_channels(self, change_id):
        return ['changes:{0}'.format(change_id)]
