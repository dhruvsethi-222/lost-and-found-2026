"""
The made-up sample data used by:  python manage.py add_sample_data

Everything here is fictional. The sample accounts all start with "sample." so they are easy
to find and remove, and the system never sends real emails to them (see core/mail.py).
The pictures are in core/sample_data/photos/, named <kind>_<colour>.jpg.
"""

PASSWORD = 'Campus-Pass-2026'

# Sample Students: short name, email, full name, admission number
STUDENTS = [
    ('kevin', 'sample.kevin.mwangi@strathmore.edu', 'Kevin Mwangi', '100101'),
    ('faith', 'sample.faith.wanjiku@strathmore.edu', 'Faith Wanjiku', '100102'),
    ('ian', 'sample.ian.kiprono@strathmore.edu', 'Ian Kiprono', '100103'),
    ('mercy', 'sample.mercy.njeri@strathmore.edu', 'Mercy Njeri', '100104'),
    ('abdi', 'sample.abdi.hassan@strathmore.edu', 'Abdi Hassan', '100105'),
    ('linet', 'sample.linet.chebet@strathmore.edu', 'Linet Chebet', '100106'),
    ('samuel', 'sample.samuel.mutua@strathmore.edu', 'Samuel Mutua', '100107'),
    ('wanjiru', 'sample.wanjiru.kamau@strathmore.edu', 'Wanjiru Kamau', '100108'),
]

# Sample Staff: short name, email, full name, staff ID, department
STAFF = [
    ('ruth', 'sample.ruth.nyambura@strathmore.edu', 'Ruth Nyambura', 'S2001', 'School of Computing'),
    ('joseph', 'sample.joseph.kariuki@strathmore.edu', 'Joseph Kariuki', 'S2002', 'Finance office'),
]

# Found items recorded at the security desk.
# key, kind, picture colour, description, days ago, place, typed place (for "other"),
# private details: serial number, marks, contents
FOUND_ITEMS = [
    ('phone1', 'phone', 'black', 'Black Samsung Galaxy A14 phone with a cracked screen protector', 3, 'library', '',
     'IMEI ends in 4471', 'Lion sticker on the back cover', ''),
    ('phone2', 'phone', 'blue', 'Blue Tecno Spark phone in a clear case', 6, 'cafeteria', '',
     '', 'Small crack in the top corner of the case', 'Folded M-Pesa receipt inside the case'),
    ('laptop1', 'laptop', 'grey', 'Grey HP laptop in a black sleeve', 2, 'computer_labs', '',
     'Serial number 5CD1234XYZ', 'Sticker removed from the lid, glue marks left', ''),
    ('laptop2', 'laptop', 'silver', 'Silver tablet with a keyboard cover', 12, 'lecture_halls', '',
     '', 'Coffee stain on the keyboard cover', ''),
    ('wallet1', 'wallet', 'brown', 'Brown leather wallet', 1, 'student_centre', '',
     '', '', 'Student ID card and KSh 500'),
    ('wallet2', 'wallet', 'red', 'Red purse with a zip', 20, 'hostels', '',
     '', 'The zip pull is broken', 'Library card and two receipts'),
    ('keys1', 'keys', 'red', 'Three keys on a red key holder', 4, 'other', 'Chapel steps',
     '', 'Initials M.N. on the key holder', ''),
    ('keys2', 'keys', 'black', 'Car key with a Toyota remote fob', 5, 'parking', '',
     '', 'Rubber cover on the fob', ''),
    ('card1', 'card', 'blue', 'Student ID card', 0, 'main_gate', '',
     '', '', 'The name on the card starts with A'),
    ('card2', 'card', 'green', 'Bank ATM card', 9, 'admin_block', '',
     'Card number ends in 0921', '', ''),
    ('bag1', 'bag', 'black', 'Black backpack with a front pocket', 4, 'library', '',
     '', 'Small football keychain on the zip', 'Two notebooks and a phone charger'),
    ('bag2', 'bag', 'green', 'Green canvas tote bag', 8, 'other', 'Bench outside the auditorium',
     '', '', 'Lunch box and a novel'),
    ('bottle1', 'bottle', 'silver', 'Silver steel water bottle', 7, 'sports', '',
     '', 'Dent near the lid', ''),
    ('bottle2', 'bottle', 'pink', 'Pink plastic flask', 15, 'cafeteria', '',
     '', 'Name sticker partly peeled off', ''),
    ('calc1', 'calculator', 'black', 'Casio fx-991ES scientific calculator', 10, 'lecture_halls', '',
     '', 'Initials B.K. scratched on the back', ''),
    ('earphones1', 'charger', 'white', 'White wireless earphones in a charging case', 8, 'library', '',
     '', 'Small scratch on the left earbud', ''),
    ('charger1', 'charger', 'black', 'Lenovo laptop charger, 65 W', 25, 'computer_labs', '',
     '', 'Blue tape around the cable near the plug', ''),
    ('hoodie1', 'clothing', 'navy', 'Navy blue hoodie, size M', 11, 'sports', '',
     '', 'Paint mark on the left sleeve', 'Gym card in the pocket'),
    ('jacket1', 'clothing', 'black', 'Black denim jacket', 30, 'student_centre', '',
     '', '', 'Bus ticket in the pocket'),
    ('watch1', 'jewellery', 'brown', 'Wristwatch with a brown leather strap', 14, 'hostels', '',
     '', 'Engraving on the back', ''),
    ('bracelet1', 'jewellery', 'gold', 'Gold-coloured bracelet', 40, 'admin_block', '',
     '', 'One link is bent', ''),
    ('umbrella1', 'umbrella', 'black', 'Large black umbrella with a curved handle', 2, 'main_gate', '',
     '', 'Small crack in the handle', ''),
    ('umbrella2', 'umbrella', 'pink', 'Small pink folding umbrella', 18, 'lecture_halls', '',
     '', '', ''),
    ('book1', 'book', 'blue', 'Introduction to Algorithms textbook', 21, 'library', '',
     '', 'A name is written inside the front cover', ''),
    ('book2', 'book', 'green', 'Green A4 notebook with accounting notes', 6, 'lecture_halls', '',
     '', 'Timetable taped inside the back cover', ''),
    ('glasses1', 'other', 'brown', 'Spectacles with brown frames', 33, 'library', '',
     '', 'The left arm is slightly loose', ''),
    # Kept more than 90 days: they appear on the Expired items page.
    ('umbrella_old', 'umbrella', 'blue', 'Blue umbrella', 120, 'cafeteria', '', '', '', ''),
    ('bottle_old', 'bottle', 'green', 'Green water bottle', 105, 'sports', '', '', 'Mountain sticker', ''),
    ('scarf_old', 'clothing', 'red', 'Red scarf', 98, 'other', 'Shuttle bus to town', '', '', ''),
    # Already handed back to their owners.
    ('phone_back', 'phone', 'white', 'White iPhone in a black case', 45, 'student_centre', '',
     'IMEI ends in 2290', 'Photo of a dog on the lock screen', ''),
    ('keys_back', 'keys', 'gold', 'Two brass keys on a ring', 52, 'hostels', '', '', 'Tag with the number 14', ''),
    ('card_back', 'card', 'red', 'Student ID card', 38, 'cafeteria', '', '', '', 'The name on the card starts with W'),
    # Disposed of after 90 days with no claim.
    ('cap_gone', 'clothing', 'grey', 'Grey cap', 140, 'sports', '', '', '', ''),
    ('bottle_gone', 'bottle', 'blue', 'Blue plastic bottle', 130, 'lecture_halls', '', '', '', ''),
]

# Lost reports from Students and Staff: owner, kind, description, days ago, place, typed place,
# and a picture for the report photo ('' = no photo)
LOST_REPORTS = [
    ('kevin', 'phone', 'Black Samsung Galaxy phone, the screen protector is cracked', 4, 'library', '', 'phone_black'),
    ('faith', 'laptop', 'Grey HP laptop in a black sleeve', 3, 'computer_labs', '', ''),
    ('ian', 'bag', 'Black backpack with notebooks and a charger inside', 5, 'library', '', 'bag_black'),
    ('mercy', 'keys', 'Three keys on a red key holder', 4, 'other', 'chapel steps', 'keys_red'),
    ('abdi', 'calculator', 'Casio fx-991ES scientific calculator', 11, 'lecture_halls', '', ''),
    ('linet', 'clothing', 'Navy hoodie, size M', 12, 'sports', '', ''),
    ('samuel', 'charger', 'White wireless earphones with the charging case', 9, 'library', '', ''),
    ('wanjiru', 'jewellery', 'Watch with a brown leather strap', 15, 'hostels', '', ''),
    ('ruth', 'book', 'Introduction to Algorithms textbook', 22, 'library', '', ''),
    ('joseph', 'keys', 'Toyota car key with a remote', 5, 'parking', '', ''),
    ('kevin', 'wallet', 'Brown leather wallet with my student ID', 1, 'student_centre', '', ''),
    ('faith', 'umbrella', 'Black umbrella with a curved handle', 3, 'main_gate', '', ''),
    ('linet', 'bottle', 'Silver steel bottle with a dent', 8, 'sports', '', ''),
    ('ian', 'bag', 'Green tote bag', 9, 'other', 'Bench outside the library', ''),
    ('abdi', 'phone', 'Nokia phone with a blue cover', 2, 'hostels', '', ''),
    ('mercy', 'clothing', 'Grey scarf', 6, 'cafeteria', '', ''),
    ('samuel', 'jewellery', 'Silver ring', 20, 'cafeteria', '', ''),
    ('wanjiru', 'wallet', 'Black wallet', 30, 'library', '', ''),
    # the lost reports of the items already handed back
    ('mercy', 'phone', 'White iPhone, black case, a dog on the lock screen', 46, 'student_centre', '', ''),
    ('samuel', 'keys', 'Two brass keys, tag number 14', 53, 'hostels', '', ''),
    ('wanjiru', 'card', 'My student ID card', 39, 'cafeteria', '', ''),
]

# Found reports from Students and Staff, and the desk item each one was handed in as.
# owner, kind, description, days ago, place, found item key
FOUND_REPORTS = [
    ('ruth', 'book', 'Green notebook with accounting notes left after my class', 6, 'lecture_halls', 'book2'),
    ('joseph', 'charger', 'Lenovo laptop charger left in the lab', 25, 'computer_labs', 'charger1'),
    ('kevin', 'card', 'Student ID card on the ground at the main gate', 0, 'main_gate', 'card1'),
    ('faith', 'umbrella', 'Pink umbrella under a desk', 18, 'lecture_halls', 'umbrella2'),
]

# Claims: claimant, found item key, answer, status, the Admin's reason, days ago
CLAIMS = [
    ('kevin', 'phone1', 'It is my Samsung A14. There is a lion sticker on the back and the IMEI ends in 4471.', 'pending', '', 2),
    ('faith', 'laptop1', 'My HP laptop. I peeled a sticker off the lid last month, so there are glue marks.', 'pending', '', 1),
    ('ian', 'bag1', 'Black backpack with two notebooks and my charger. There is a small football keychain on the zip.', 'pending', '', 3),
    ('abdi', 'calc1', 'My Casio fx-991ES that I use for engineering maths.', 'more_evidence',
     'Is there anything written or scratched on it?', 9),
    ('wanjiru', 'watch1', 'A brown leather strap watch my father gave me.', 'more_evidence', 'What is engraved on the back?', 12),
    ('kevin', 'wallet1', 'Brown wallet with my student ID and about 500 shillings inside.', 'approved',
     'The student ID inside matches the claimant', 1),
    ('faith', 'umbrella1', 'Large black umbrella, the handle has a crack.', 'approved', 'Described the cracked handle', 1),
    ('linet', 'bottle1', 'Steel bottle with a dent near the lid.', 'approved', 'Described the dent correctly', 6),
    ('abdi', 'wallet1', 'A brown wallet.', 'closed', 'Another claim for this item was approved', 1),
    ('samuel', 'book1', 'My algorithms textbook.', 'rejected', 'The name inside the cover does not match', 18),
    ('mercy', 'hoodie1', 'Navy hoodie I lost at the gym.', 'rejected', 'Could not say what was in the pocket', 9),
    # the items already handed back
    ('mercy', 'phone_back', 'White iPhone with a photo of my dog on the lock screen, IMEI ends in 2290.', 'approved',
     'IMEI and lock screen match', 44),
    ('samuel', 'keys_back', 'Two brass keys with a tag numbered 14 for my hostel room.', 'approved', 'Tag number matches', 50),
    ('wanjiru', 'card_back', 'My student ID card, my name starts with W.', 'approved', 'Name and photo match the claimant', 37),
]

# Items handed back: found item key, days ago
HAND_OVERS = [('phone_back', 43), ('keys_back', 49), ('card_back', 36)]

# Items disposed of: found item key, reason, days ago
DISPOSALS = [
    ('cap_gone', 'Kept for more than 90 days with no claim. Given to charity.', 40),
    ('bottle_gone', 'Kept for more than 90 days with no claim. Recycled.', 35),
]

# Posts and replies: author, text, days ago, and the replies to it (author, text, days ago)
POSTS = [
    ('kevin', 'Has anyone seen a black Samsung phone in the library? I left it on the second floor this morning.', 4,
     [('faith', 'Check with the security desk. They record everything that is handed in.', 4)]),
    ('mercy', 'Lost three keys on a red key holder near the chapel. Please hand them to security if you find them.', 4, []),
    ('ruth', 'Reminder: items left in lecture halls after evening classes go to the security desk every morning.', 7,
     [('ian', 'Thank you, that helps.', 7)]),
    ('linet', 'Lost a navy hoodie at the sports complex on Tuesday. Size M.', 12, []),
    ('joseph', 'The Finance office has a lost property box too. We take everything to the security desk on Fridays.', 20,
     [('samuel', 'Good to know, thanks.', 19)]),
    ('abdi', 'How long does the desk keep items? I lost my calculator before exams.', 11,
     [('wanjiru', 'I think it is 90 days. The search on this site shows everything at the desk.', 11)]),
]
