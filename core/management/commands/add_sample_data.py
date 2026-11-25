"""
Fills the site with made-up lost and found items, so it looks like a site that is in use.

    python manage.py add_sample_data            adds the sample data
    python manage.py add_sample_data --remove   takes it all out again

It adds 10 sample accounts (8 Students, 2 Staff), 34 found items with pictures and private details,
25 reports, 14 claims, 3 hand-overs, 2 disposals and 10 posts and replies, then works out the matches.
It works on SQLite and MySQL, never changes or deletes anything that was already there,
and sends no emails. The data is in core/sample_data/sample_items.py.
"""
from datetime import timedelta
from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.core.files import File
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from accounts.models import Role, User
from claims.models import Claim
from core.sample_data import sample_items as data
from handover.models import HandOver
from items.models import FoundItem, ItemReport, VerificationDetail
from matching.matcher import rank_matches, score_pair
from matching.models import Match
from posts.models import Post

PHOTOS = Path(__file__).resolve().parent.parent.parent / 'sample_data' / 'photos'
SAMPLE_PHOTO_START = 'found_items/sample_'      # every sample found-item photo starts like this


def days_ago(days):
    """The date and time a number of days ago (in the morning, so it is never in the future)."""
    moment = timezone.now() - timedelta(days=days)
    return moment.replace(hour=9, minute=30) if days > 0 else moment


def date_ago(days):
    return timezone.localdate() - timedelta(days=days)


class Command(BaseCommand):
    help = 'Add made-up lost and found items to the site (or take them out with --remove).'

    def add_arguments(self, parser):
        parser.add_argument('--remove', action='store_true', help='Take the sample data out again.')

    def handle(self, *args, **options):
        if options['remove']:
            self.remove()
            return

        # 1. Only once: stop if the sample accounts are already there.
        if User.objects.filter(email__startswith='sample.').exists():
            raise CommandError('The sample data is already there. To start again, run: '
                               'python manage.py add_sample_data --remove')

        # 2. The security officer who recorded the items.
        officer = User.objects.filter(role=Role.ADMIN).order_by('id').first()
        if officer is None:
            raise CommandError('Create a security officer first: python manage.py createofficer ...')

        # 3. Add everything in one go: if one step fails, nothing is saved.
        with transaction.atomic():
            people = self.add_accounts()
            items = self.add_found_items(officer)
            self.add_reports(people, items)
            matches = self.add_matches(items)
            self.add_claims(people, items, officer)
            self.add_hand_overs(items, officer)
            self.add_disposals(items, officer)
            self.add_posts(people)

        self.stdout.write(self.style.SUCCESS(
            f'Added {len(people)} sample accounts, {len(items)} found items, '
            f'{len(data.LOST_REPORTS) + len(data.FOUND_REPORTS)} reports, {len(data.CLAIMS)} claims, '
            f'{matches} matches and {sum(1 + len(p[3]) for p in data.POSTS)} posts. '
            f'Sample accounts use the password {data.PASSWORD}.'))

    # ------------------------------------------------------------------ the steps

    def add_accounts(self):
        """The sample Students and Staff, already verified. Returns them by short name, e.g. people['kevin']."""
        people = {}
        for short, email, name, admission_no in data.STUDENTS:
            people[short] = User.objects.create_user(email, data.PASSWORD, name=name, role=Role.STUDENT,
                                                     admission_no=admission_no, is_verified=True)
        for short, email, name, staff_no, department in data.STAFF:
            people[short] = User.objects.create_user(email, data.PASSWORD, name=name, role=Role.STAFF,
                                                     staff_no=staff_no, department=department, is_verified=True)
        return people

    def add_found_items(self, officer):
        """The items at the desk, each with a picture and its private details. Returns them by key."""
        items = {}
        for key, kind, colour, description, days, place, typed_place, serial, marks, contents in data.FOUND_ITEMS:
            # copy the picture into the media folder under a new random name
            with open(PHOTOS / f'{kind}_{colour}.jpg', 'rb') as picture:
                photo_name = default_storage.save(f'{SAMPLE_PHOTO_START}{uuid4().hex}.jpg', File(picture))
            item = FoundItem.objects.create(recorded_by=officer, category=kind, description=description,
                                            place=place, place_other=typed_place, date_found=date_ago(days),
                                            photo=photo_name)
            FoundItem.objects.filter(pk=item.pk).update(created_at=days_ago(days))   # recorded on that day
            VerificationDetail.objects.create(found_item=item, serial_no=serial, marks=marks, contents=contents)
            items[key] = item
        return items

    def add_reports(self, people, items):
        """Lost and found reports from the sample Students and Staff."""
        for owner, kind, description, days, place, typed_place, picture in data.LOST_REPORTS:
            report = ItemReport.objects.create(user=people[owner], type='lost', category=kind, description=description,
                                               date=date_ago(days), place=place, place_other=typed_place)
            if picture:                                  # an optional report photo (kept private)
                with open(PHOTOS / f'{picture}.jpg', 'rb') as photo:
                    report.photo.save('report.jpg', File(photo))
            ItemReport.objects.filter(pk=report.pk).update(created_at=days_ago(days))

        for owner, kind, description, days, place, item_key in data.FOUND_REPORTS:
            report = ItemReport.objects.create(user=people[owner], type='found', category=kind,
                                               description=description, date=date_ago(days), place=place)
            ItemReport.objects.filter(pk=report.pk).update(created_at=days_ago(days))
            # the desk item this report became (update() changes only this column)
            FoundItem.objects.filter(pk=items[item_key].pk).update(handed_in_report=report)

    def add_matches(self, items):
        """
        Works out the matches the same way the system does (matching/matcher.py),
        but without sending any match alert emails. Returns how many were saved.
        """
        saved = 0
        disposed = [key for key, reason, days in data.DISPOSALS]
        for key, item in items.items():
            if key in disposed:                          # nobody claimed these, so they had no matches
                continue
            for report in ItemReport.objects.filter(type='lost', category=item.category):
                score = score_pair(report, item)
                if score >= settings.MATCH_MINIMUM_SCORE:
                    Match.objects.get_or_create(report=report, found_item=item, defaults={'score': score})
                    saved += 1
            rank_matches(item)
        return saved

    def add_claims(self, people, items, officer):
        """Claims in every status. The item of an approved claim becomes Claimed."""
        for claimant, item_key, answer, status, reason, days in data.CLAIMS:
            item = items[item_key]
            claim = Claim.objects.create(found_item=item, user=people[claimant], answers=answer)
            Claim.objects.filter(pk=claim.pk).update(created_at=days_ago(days + 1))
            if status == 'pending':
                continue
            # the Admin's decision (for "more details needed", the reason is the question asked)
            Claim.objects.filter(pk=claim.pk).update(status=status, reason=reason, decided_by=officer,
                                                     decided_at=days_ago(days))
            if status == 'approved':
                FoundItem.objects.filter(pk=item.pk).update(status=FoundItem.Status.CLAIMED)

    def add_hand_overs(self, items, officer):
        """Approved claims that were collected: the item becomes Returned."""
        for item_key, days in data.HAND_OVERS:
            item = items[item_key]
            claim = Claim.objects.get(found_item=item, status='approved')
            hand_over = HandOver.objects.create(claim=claim, released_by=officer,
                                                collector_id=claim.user.admission_no or claim.user.staff_no)
            HandOver.objects.filter(pk=hand_over.pk).update(date=days_ago(days))
            FoundItem.objects.filter(pk=item.pk).update(status=FoundItem.Status.RETURNED)

    def add_disposals(self, items, officer):
        """Items kept too long: disposed of, and their private details deleted (as the system does)."""
        for item_key, reason, days in data.DISPOSALS:
            item = items[item_key]
            FoundItem.objects.filter(pk=item.pk).update(status=FoundItem.Status.DISPOSED, disposed_by=officer,
                                                        disposed_at=days_ago(days), disposal_reason=reason)
            VerificationDetail.objects.filter(found_item=item).delete()

    def add_posts(self, people):
        for author, text, days, replies in data.POSTS:
            post = Post.objects.create(user=people[author], text=text)
            Post.objects.filter(pk=post.pk).update(date=days_ago(days))
            for reply_author, reply_text, reply_days in replies:
                reply = Post.objects.create(user=people[reply_author], text=reply_text, reply_to=post)
                Post.objects.filter(pk=reply.pk).update(date=days_ago(reply_days) + timedelta(hours=2))

    # ------------------------------------------------------------------ taking it out again

    def remove(self):
        """Deletes the sample accounts, the sample items and everything linked to them. Nothing else."""
        people = User.objects.filter(email__startswith='sample.')
        items = FoundItem.objects.filter(photo__startswith=SAMPLE_PHOTO_START)
        if not people.exists() and not items.exists():
            self.stdout.write('There is no sample data to remove.')
            return

        with transaction.atomic():
            # the order matters: hand-overs, then claims, then items, then reports, posts and accounts
            linked = Q(claim__user__in=people) | Q(claim__found_item__in=items)
            HandOver.objects.filter(linked).delete()
            Claim.objects.filter(Q(user__in=people) | Q(found_item__in=items)).delete()
            for item in items:
                item.photo.delete(save=False)            # the picture file too
                item.delete()                            # its matches and private details go with it
            for report in ItemReport.objects.filter(user__in=people):
                if report.photo:
                    report.photo.delete(save=False)
                report.delete()
            Post.objects.filter(user__in=people).delete()
            count = people.count()
            people.delete()
        self.stdout.write(self.style.SUCCESS(f'Removed the sample data ({count} sample accounts and their items).'))
