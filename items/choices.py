"""
Fixed lists for the dropdowns (NFR-03). Everyone picks from the same list, so a
"wallet" reported by a Student and a "wallet" recorded by the Admin are spelled the
same way, which the matching in Dev 2 needs.
The left value is stored in the database; the right value is what people see.
"""
from django.db import models


class Category(models.TextChoices):
    BAG = 'bag', 'Bag or backpack'
    BOOK = 'book', 'Book or notes'
    BOTTLE = 'bottle', 'Bottle or flask'
    CALCULATOR = 'calculator', 'Calculator'
    CARD = 'card', 'ID or bank card'
    CHARGER = 'charger', 'Charger or earphones'
    CLOTHING = 'clothing', 'Clothing'
    JEWELLERY = 'jewellery', 'Jewellery or watch'
    KEYS = 'keys', 'Keys'
    LAPTOP = 'laptop', 'Laptop or tablet'
    PHONE = 'phone', 'Phone'
    UMBRELLA = 'umbrella', 'Umbrella'
    WALLET = 'wallet', 'Wallet or purse'
    OTHER = 'other', 'Other'


class Place(models.TextChoices):
    LIBRARY = 'library', 'Library'
    STUDENT_CENTRE = 'student_centre', 'Student Centre'
    CAFETERIA = 'cafeteria', 'Cafeteria'
    LECTURE_HALLS = 'lecture_halls', 'Lecture halls'
    STAFF_OFFICES = 'staff_offices', 'Staff offices'
    COMPUTER_LABS = 'computer_labs', 'Computer labs'
    SPORTS = 'sports', 'Sports complex'
    HOSTELS = 'hostels', 'Hostels'
    PARKING = 'parking', 'Parking'
    ADMIN_BLOCK = 'admin_block', 'Administration block'
    MAIN_GATE = 'main_gate', 'Main gate'
    OTHER = 'other', 'Other'
