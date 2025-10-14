from django.db import models

class Hiring_process(models.Model):
    INTEGRATION_CHOICES = [
        ("google_sheet", "Google Sheet"),
        ("typeform", "Typeform"),
        ("surveymonkey", "SurveyMonkey"),
    ]

    integration_type = models.CharField(max_length=50, choices=INTEGRATION_CHOICES, db_index=True)
    name = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    identifier = models.CharField(max_length=255, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    token = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=["integration_type"]),
            models.Index(fields=["name"]),
            models.Index(fields=["identifier"]),
            models.Index(fields=["created_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.integration_type}: {self.name or self.identifier}"




class TypeformAnswer(models.Model):
    integration = models.ForeignKey(
        'Hiring_process', 
        on_delete=models.CASCADE, 
        related_name="typeform_answers"
    )
    response_id = models.CharField(max_length=255, db_index=True)
     # ========== PERSONAL DETAILS ==========
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    language = models.JSONField(blank=True, null=True)
    job_responsibilities = models.CharField(max_length=255, blank=True, null=True)
    company = models.CharField(max_length=255, blank=True, null=True)

    # ========== EXPERIENCE / EDUCATION ==========
    experience = models.CharField(max_length=50, blank=True, null=True)
    notice_period = models.BooleanField(default=False)
    joining_date = models.DateTimeField(blank=True, null=True)

    # ========== EDUCATION DETAILS ==========
    highest_degree = models.CharField(max_length=100, blank=True, null=True)
    specialization = models.CharField(max_length=100, blank=True, null=True)
    university = models.CharField(max_length=255, blank=True, null=True)
    percentage = models.CharField(max_length=10, blank=True, null=True)

    # ========== SKILLS ==========
    python = models.BooleanField(default=False)
    python_rate = models.IntegerField(blank=True, null=True)
    rdbms = models.BooleanField(default=False)
    rdbms_rate = models.IntegerField(blank=True, null=True)
    machine_learning = models.BooleanField(default=False)
    machine_learning_rate = models.IntegerField(blank=True, null=True)
    r_language = models.BooleanField(default=False)
    r_language_rate = models.IntegerField(blank=True, null=True)
    rave_developer = models.BooleanField(default=False)
    rave_developer_rate = models.IntegerField(blank=True, null=True)
    cucumber = models.BooleanField(default=False)
    cucumber_rate = models.IntegerField(blank=True, null=True)
    bdd = models.BooleanField(default=False)
    bdd_rate = models.IntegerField(blank=True, null=True)

    # ========== MATHS SKILLS ==========
    linear_programming = models.BooleanField(default=False)
    linear_programming_rate = models.IntegerField(blank=True, null=True)
    statistics_probability = models.BooleanField(default=False)
    statistics_probability_rate = models.IntegerField(blank=True, null=True)
    discrete_mathematics = models.BooleanField(default=False)
    discrete_mathematics_rate = models.IntegerField(blank=True, null=True)

    # ========== MISC ==========
    unmapped_fields = models.JSONField(blank=True, null=True)
    landed_at = models.DateTimeField()
    submitted_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Typeform Answer {self.response_id}"

