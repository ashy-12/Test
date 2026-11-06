import csv
import io
from datetime import datetime
from django.db import transaction
from django.core.validators import validate_email
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from .models import Student


COLUMN_ALIASES = {
    'roll_number': ['roll_number', 'roll_no', 'rollno', 'roll number', 'roll', 'student_id', 'id'],
    'first_name': ['first_name', 'firstname', 'first name', 'fname'],
    'last_name': ['last_name', 'lastname', 'last name', 'lname', 'surname'],
    'email': ['email', 'email_address', 'email address'],
    'course': ['course', 'department', 'dept', 'major', 'program'],
    'gender': ['gender', 'sex'],
    'phone': ['phone', 'phone_number', 'mobile', 'contact'],
    'date_of_birth': ['date_of_birth', 'dob', 'birth_date', 'birthdate'],
    'enrollment_date': ['enrollment_date', 'admission_date', 'joining_date', 'enrolled_on'],
    'address': ['address', 'residence', 'city'],
}


def parse_date(date_str):
    if not date_str or not date_str.strip():
        return None
    date_str = date_str.strip()
    formats = ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y', '%Y/%m/%d']
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None


def generate_sample_csv():
    """Generates a sample CSV template for bulk student import."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'roll_number', 'first_name', 'last_name', 'email', 'department',
        'gender', 'phone', 'date_of_birth', 'enrollment_date', 'address'
    ])
    writer.writerow([
        'CS-2026-101', 'Arjun', 'Mehta', 'arjun.mehta@example.com', 'Computer Science',
        'Male', '+91 98123 45678', '2004-03-12', '2024-08-01', '42 Linking Road, Mumbai'
    ])
    writer.writerow([
        'IT-2026-102', 'Meera', 'Nair', 'meera.nair@example.com', 'Information Technology',
        'Female', '+91 98234 56781', '2004-07-25', '2024-08-01', '18 Marine Drive, Kochi'
    ])
    writer.writerow([
        'DS-2026-103', 'Vikram', 'Rao', 'vikram.rao@example.com', 'Data Science',
        'Male', '+91 98345 67892', '2003-11-15', '2023-08-01', '90 Indiranagar, Bangalore'
    ])
    return output.getvalue()


def parse_and_import_students_csv(file_obj):
    """
    Parses and validates an uploaded CSV file, creating Student records in bulk.
    Uses atomic transaction so that if any row is invalid, everything rolls back.

    Returns:
        tuple: (success: bool, imported_count: int, error_messages: list[str])
    """
    errors = []

    # 1. Validate file extension
    file_name = getattr(file_obj, 'name', '')
    if not file_name.lower().endswith('.csv'):
        return False, 0, ["Invalid file type. Only .csv files are supported."]

    # 2. Read and decode content
    try:
        raw_bytes = file_obj.read()
        if not raw_bytes:
            return False, 0, ["The uploaded CSV file is empty."]

        # Handle UTF-8 with BOM or standard UTF-8
        try:
            decoded_text = raw_bytes.decode('utf-8-sig')
        except UnicodeDecodeError:
            decoded_text = raw_bytes.decode('latin-1')

    except Exception as e:
        return False, 0, [f"Failed to read file: {str(e)}"]

    # 3. Read CSV
    csv_file = io.StringIO(decoded_text)
    reader = csv.reader(csv_file)

    try:
        headers = next(reader)
    except StopIteration:
        return False, 0, ["CSV file contains no headers or rows."]

    # Map headers to canonical fields
    header_map = {}
    normalized_headers = [h.strip().lower() for h in headers]

    for canonical, aliases in COLUMN_ALIASES.items():
        for idx, h in enumerate(normalized_headers):
            if h in aliases:
                header_map[canonical] = idx
                break

    # Check required columns
    required_cols = ['roll_number', 'first_name', 'last_name', 'email', 'course']
    missing_cols = [c for c in required_cols if c not in header_map]
    if missing_cols:
        return False, 0, [f"Missing required CSV column(s): {', '.join(missing_cols)}. Please check the column headers."]

    # Existing records in database for uniqueness check
    existing_rolls = set(Student.objects.values_list('roll_number', flat=True))
    existing_emails = set(Student.objects.values_list('email', flat=True))

    seen_rolls = set()
    seen_emails = set()
    students_to_create = []

    # Valid course choices mapping
    valid_courses = {c[0].lower(): c[0] for c in Student.COURSE_CHOICES}

    row_index = 1  # 1 is header
    for row in reader:
        row_index += 1
        if not row or all(not str(cell).strip() for cell in row):
            continue  # Skip blank rows

        def get_val(canonical_name):
            if canonical_name in header_map and header_map[canonical_name] < len(row):
                return row[header_map[canonical_name]].strip()
            return ''

        roll_number = get_val('roll_number')
        first_name = get_val('first_name')
        last_name = get_val('last_name')
        email = get_val('email')
        course_raw = get_val('course')
        gender_raw = get_val('gender')
        phone = get_val('phone')
        dob_raw = get_val('date_of_birth')
        enrollment_raw = get_val('enrollment_date')
        address = get_val('address')

        # Row validations
        if not roll_number:
            errors.append(f"Row {row_index}: Roll Number is missing.")
        elif roll_number in seen_rolls:
            errors.append(f"Row {row_index}: Duplicate Roll Number '{roll_number}' inside the CSV file.")
        elif roll_number in existing_rolls:
            errors.append(f"Row {row_index}: Student with Roll Number '{roll_number}' already exists in database.")
        else:
            seen_rolls.add(roll_number)

        if not first_name:
            errors.append(f"Row {row_index}: First Name is required.")

        if not last_name:
            errors.append(f"Row {row_index}: Last Name is required.")

        if not email:
            errors.append(f"Row {row_index}: Email Address is missing.")
        else:
            try:
                validate_email(email)
                if email in seen_emails:
                    errors.append(f"Row {row_index}: Duplicate Email '{email}' inside the CSV file.")
                elif email in existing_emails:
                    errors.append(f"Row {row_index}: Student with Email '{email}' already exists in database.")
                else:
                    seen_emails.add(email)
            except DjangoValidationError:
                errors.append(f"Row {row_index}: Invalid email format '{email}'.")

        if not course_raw:
            errors.append(f"Row {row_index}: Department/Course is missing.")
        else:
            course_match = valid_courses.get(course_raw.lower())
            course = course_match if course_match else course_raw

        # Gender validation
        gender = 'Other'
        if gender_raw:
            g_low = gender_raw.lower()
            if g_low in ['m', 'male']:
                gender = 'Male'
            elif g_low in ['f', 'female']:
                gender = 'Female'
            else:
                gender = 'Other'

        # Date validations
        dob = parse_date(dob_raw) if dob_raw else None
        if dob_raw and not dob:
            errors.append(f"Row {row_index}: Invalid date format for Date of Birth ('{dob_raw}'). Use YYYY-MM-DD or DD/MM/YYYY.")

        enrollment_date = parse_date(enrollment_raw) if enrollment_raw else timezone.now().date()
        if enrollment_raw and not parse_date(enrollment_raw):
            errors.append(f"Row {row_index}: Invalid date format for Enrollment Date ('{enrollment_raw}'). Use YYYY-MM-DD.")

        # Prepare Student instance
        students_to_create.append(Student(
            roll_number=roll_number,
            first_name=first_name,
            last_name=last_name,
            email=email,
            course=course if course_raw else 'Computer Science',
            gender=gender,
            phone=phone,
            date_of_birth=dob,
            enrollment_date=enrollment_date,
            address=address,
        ))

    # 4. Atomic Transaction Enforcement
    if errors:
        return False, 0, errors

    if not students_to_create:
        return False, 0, ["No student records found to import in the CSV."]

    try:
        with transaction.atomic():
            Student.objects.bulk_create(students_to_create)
        return True, len(students_to_create), []
    except Exception as e:
        return False, 0, [f"Transaction failed and was rolled back: {str(e)}"]
