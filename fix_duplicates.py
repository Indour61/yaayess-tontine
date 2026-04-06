from cotisationtontine.models import Versement
from django.db.models import Count

duplicates = (
    Versement.objects
    .values("member", "cycle", "tour")
    .annotate(c=Count("id"))
    .filter(c__gt=1)
)

for d in duplicates:
    qs = Versement.objects.filter(
        member=d["member"],
        cycle=d["cycle"],
        tour=d["tour"]
    ).order_by("date_creation")

    print("Correction membre", d["member"])

    keep = qs.first()

    for v in qs.exclude(id=keep.id):
        print("Suppression ID", v.id)
        v.delete()

