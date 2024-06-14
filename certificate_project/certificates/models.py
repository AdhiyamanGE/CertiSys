from django.db import models
from django.contrib import admin


class Student(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=100)
    certificate_issued = models.BooleanField(default=False)


admin.site.register(Student)
