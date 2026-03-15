from django.db import models

class GeneratedVideo(models.Model):
    title = models.CharField(max_length=200)
    script = models.TextField()
    video_file = models.FileField(upload_to="videos/")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
