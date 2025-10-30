from rest_framework import serializers
from .models import Skills, Job


class SkillsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skills
        fields = ['id', 'name']


class JobSerializer(serializers.ModelSerializer):
    Skills_Required = SkillsSerializer(many=True, read_only=True)
    skill_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Skills.objects.all(), write_only=True
    )

    class Meta:
        model = Job
        fields = [
            'id',
            'Job_Title',
            'Experience_In_Years',
            'Description',
            'Job_Type',
            'Job_Location',
            'no_of_opening',
            'Skills_Required',
            'skill_ids',
        ]

    def create(self, validated_data):
        skill_ids = validated_data.pop('skill_ids', [])
        job = Job.objects.create(**validated_data)
        job.Skills_Required.set(skill_ids)
        return job

    def update(self, instance, validated_data):
        skill_ids = validated_data.pop('skill_ids', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if skill_ids is not None:
            instance.Skills_Required.set(skill_ids)
        return instance
