from django.db import models


class Cause(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(unique=True)
    description = models.CharField(max_length=200, blank=True)
    partner_charity = models.CharField(max_length=120, blank=True, help_text="The registered charity that receives the money.")
    weight = models.PositiveSmallIntegerField(default=1, help_text="Share of each donation. Weights 2 and 1 split money 2:1.")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.name


class LedgerQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise RuntimeError("The donation ledger is append-only. Add a new entry instead.")

    def delete(self):
        raise RuntimeError("The donation ledger is append-only. Add a new entry instead.")


class LedgerEntry(models.Model):
    """One line in the permanent donation ledger. Rows are never edited or deleted; mistakes get a reversal row."""

    class Type(models.TextChoices):
        ACCRUED = "accrued", "Set aside"
        REVERSAL = "reversal", "Reversed (refund)"

    order = models.ForeignKey("orders.Order", on_delete=models.PROTECT, related_name="ledger_entries")
    cause = models.ForeignKey(Cause, on_delete=models.PROTECT, related_name="ledger_entries")
    amount_minor = models.IntegerField(help_text="Paise. Negative for reversals.")
    entry_type = models.CharField(max_length=10, choices=Type.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = LedgerQuerySet.as_manager()

    class Meta:
        ordering = ["id"]
        verbose_name_plural = "ledger entries"
        constraints = [models.UniqueConstraint(fields=["order", "cause", "entry_type"], name="uniq_ledger_entry")]

    def __str__(self):
        return f"{self.entry_type} {self.amount_minor} for {self.cause}"

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise RuntimeError("Ledger entries cannot be edited. Add a new entry instead.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise RuntimeError("Ledger entries cannot be deleted.")


class Disbursement(models.Model):
    """Money actually sent to a charity partner. Attach the receipt so the Impact page can prove it."""

    cause = models.ForeignKey(Cause, on_delete=models.PROTECT, related_name="disbursements")
    charity_name = models.CharField(max_length=120)
    amount_minor = models.PositiveIntegerField(help_text="In paise.")
    paid_on = models.DateField()
    reference = models.CharField(max_length=120, help_text="Bank or UPI reference.")
    proof = models.FileField(upload_to="disbursements/", blank=True, help_text="Receipt or report (PDF or image).")
    note = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-paid_on", "-id"]

    def __str__(self):
        return f"{self.charity_name} {self.amount_minor} on {self.paid_on}"
