from django.db import models
class Skills(models.Model):
    name = models.CharField(max_length=100, unique=True, db_index=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'skills'

class Job(models.Model):
    Job_Title = models.CharField(max_length=255,db_index=True)
    Experience_In_Years = models.TextField(db_index=True)
    Description = models.CharField(max_length=255,db_index=True)
    Job_Type = models.CharField(max_length=100,db_index=True)
    Job_Location = models.CharField(max_length=255,db_index=True)
    no_of_opening = models.IntegerField(db_index=True)
    Skills_Required = models.ManyToManyField(Skills, related_name='jobs')

    def __str__(self):
        return self.Job_Title

    class Meta:
        db_table = 'job_listings'