from rest_framework import serializers
from .models import CandidateDetails, CandidateStatusHistory

class CandidateStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CandidateStatusHistory
        fields = ['id', 'previous_status', 'new_status', 'changed_at']


class CandidateDetailsSerializer(serializers.ModelSerializer):
    history = CandidateStatusHistorySerializer(many=True, read_only=True)

    class Meta:
        model = CandidateDetails
        fields = [
            'id',
            'TypeformAnswer',
            'current_status',
            'interview_date',
            'offer_letter_given',
            'joining_date',
            'created_at',
            'updated_at',
            'history'
        ]

    def validate(self, data):
        instance = getattr(self, 'instance', None)
        old_status = getattr(instance, 'current_status', 'scouting')
        new_status = data.get('current_status', old_status)

        allowed_transitions = {
            'scouting': ['ongoing'],
            'ongoing': ['hired', 'recycle'],
            'hired': [],
            'recycle': []
        }

        if old_status != new_status:
            allowed_next = allowed_transitions.get(old_status, [])
            if new_status not in allowed_next:
                raise serializers.ValidationError({
                    "current_status": f"'{old_status}' से '{new_status}' transition allowed नहीं है। Allowed next status: {allowed_next}"
                })

        if new_status == 'ongoing':
            if not data.get('interview_date') and not getattr(instance, 'interview_date', None):
                raise serializers.ValidationError({
                    'interview_date': 'Ongoing status के लिए interview_date जरूरी है।'
                })

        if new_status == 'hired':
            if not data.get('offer_letter_given', getattr(instance, 'offer_letter_given', False)):
                raise serializers.ValidationError({
                    'offer_letter_given': 'Hired status के लिए offer_letter_given True होना चाहिए।'
                })
            if not data.get('joining_date') and not getattr(instance, 'joining_date', None):
                raise serializers.ValidationError({
                    'joining_date': 'Hired status के लिए joining_date देना जरूरी है।'
                })

        return data
