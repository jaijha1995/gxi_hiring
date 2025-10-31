from django.db import models

# Create your models here.


class Skills(models.Model):
    name = models.CharField(max_length=100, unique=True, db_index=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'skills'


class Department(models.Model):
    name = models.CharField(max_length=100, unique=True, db_index=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'Departments'


class Job_types(models.Model):
    name = models.CharField(max_length=100, unique=True, db_index=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'Job_types'

class Job(models.Model):
    Job_Title = models.CharField(max_length=255,db_index=True)
    Experience_In_Years = models.IntegerField(db_index=True)
    Description = models.TextField()
    department = models.ForeignKey(Department, on_delete=models.CASCADE, db_index=True , null=True, blank=True)
    Job_Type = models.ForeignKey(Job_types, on_delete=models.CASCADE, db_index=True, null=True, blank=True)
    Job_Location = models.CharField(max_length=255,db_index=True)
    no_of_opening = models.IntegerField(db_index=True)
    Targerted_Hiring_Date = models.DateField(null=True, blank=True, db_index=True)
    Skills_Required = models.ManyToManyField(Skills, related_name='jobs')

    def __str__(self):
        return self.Job_Title

    class Meta:
        db_table = 'job_listings'