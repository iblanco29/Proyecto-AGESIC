from django.db import models

# Create your models here.

class User(models.Model):
	name = models.CharField(max_length=100)
	surname = models.CharField(max_length=100)
	idNumber = models.TextField(max_length=12)
	date = models.DateTimeField(auto_now_add=True)
	result = models.BooleanField() 

class allowedUsers(models.Model):
	name = models.CharField(max_length=100)
	surname = models.CharField(max_length=100)
	idNumber = models.TextField(max_length=12)
		