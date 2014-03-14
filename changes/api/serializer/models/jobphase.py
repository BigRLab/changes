from changes.api.serializer import Serializer, register
from changes.models import JobPhase


@register(JobPhase)
class JobPhaseSerializer(Serializer):
    def serialize(self, instance, attrs):
        return {
            'id': instance.id.hex,
            'name': instance.label,
            'result': instance.result,
            'status': instance.status,
            'duration': instance.duration,
            'dateCreated': instance.date_created,
            'dateStarted': instance.date_started,
            'dateFinished': instance.date_finished,
        }


class JobPhaseWithStepsSerializer(JobPhaseSerializer):
    def serialize(self, instance, attrs):
        data = super(JobPhaseWithStepsSerializer, self).serialize(instance, attrs)
        data['steps'] = list(instance.steps)
        return data
