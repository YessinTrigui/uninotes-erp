from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Avg, Count, Sum, Q, F, FloatField, ExpressionWrapper
from catalog.models import Subject
from .models import Enrollment, CartItem, Grade


def subject_catalog_view(request):
    if not request.user.is_authenticated or not request.user.is_student():
        return redirect('login')

    current_semester = request.user.current_semester

    if current_semester is None:
        messages.warning(request, 'No semester has been assigned to your account. Contact an administrator.')
        all_subjects = Subject.objects.none()
        recommended_subjects = Subject.objects.none()
    else:
        all_subjects = Subject.objects.filter(
            semester=current_semester
        ).select_related('responsible_tutor', 'semester__specialization')

        enrolled_subject_ids = Enrollment.objects.filter(
            student=request.user,
            status__in=[Enrollment.STATUS_CONFIRMED, Enrollment.STATUS_DROPPED],
        ).values_list('subject_id', flat=True)

        cart_subject_ids = CartItem.objects.filter(
            student=request.user,
        ).values_list('subject_id', flat=True)

        excluded_ids = list(enrolled_subject_ids) + list(cart_subject_ids)

        recommended_subjects = all_subjects.exclude(
            id__in=excluded_ids
        ).order_by('-is_mandatory', 'name')[:5]

    cart_items = CartItem.objects.filter(student=request.user).select_related('subject')

    cart_subject_id_set = set(cart_items.values_list('subject_id', flat=True))

    confirmed_subject_id_set = set(
        Enrollment.objects.filter(
            student=request.user,
            status=Enrollment.STATUS_CONFIRMED,
        ).values_list('subject_id', flat=True)
    )

    context = {
        'all_subjects': all_subjects,
        'recommended_subjects': recommended_subjects,
        'cart_subject_ids': cart_subject_id_set,
        'confirmed_subject_ids': confirmed_subject_id_set,
        'current_semester': current_semester,
        'cart_item_count': cart_items.count(),
    }

    return render(request, 'enrollment/catalog.html', context)


def add_to_cart_view(request, subject_id):
    if not request.user.is_authenticated or not request.user.is_student():
        return redirect('login')

    if request.method != 'POST':
        return redirect('subject_catalog')

    subject = get_object_or_404(Subject, id=subject_id)

    already_enrolled = Enrollment.objects.filter(
        student=request.user,
        subject=subject,
        status=Enrollment.STATUS_CONFIRMED,
    ).exists()

    if already_enrolled:
        messages.warning(request, f'You are already confirmed in "{subject.name}".')
        return redirect('subject_catalog')

    already_in_cart = CartItem.objects.filter(
        student=request.user,
        subject=subject,
    ).exists()

    if already_in_cart:
        messages.warning(request, f'"{subject.name}" is already in your cart.')
        return redirect('subject_catalog')

    if not subject.has_available_seats():
        messages.error(request, f'"{subject.name}" is full. No seats available.')
        return redirect('subject_catalog')

    CartItem.objects.create(student=request.user, subject=subject)
    messages.success(request, f'"{subject.name}" added to your cart.')
    return redirect('subject_catalog')


def remove_from_cart_view(request, item_id):
    if not request.user.is_authenticated or not request.user.is_student():
        return redirect('login')

    if request.method != 'POST':
        return redirect('cart')

    cart_item = get_object_or_404(CartItem, id=item_id, student=request.user)
    subject_name = cart_item.subject.name
    cart_item.delete()
    messages.success(request, f'"{subject_name}" removed from your cart.')
    return redirect('cart')


def cart_view(request):
    if not request.user.is_authenticated or not request.user.is_student():
        return redirect('login')

    current_semester = request.user.current_semester
    cart_items = CartItem.objects.filter(student=request.user).select_related('subject')

    cart_credits = cart_items.aggregate(total=Sum('subject__credits'))['total'] or 0
    confirmed_credits = 0
    credit_limit = 0

    if current_semester:
        credit_limit = current_semester.credit_limit
        confirmed_credits = Enrollment.objects.filter(
            student=request.user,
            status=Enrollment.STATUS_CONFIRMED,
            subject__semester=current_semester,
        ).aggregate(total=Sum('subject__credits'))['total'] or 0

    total_used = confirmed_credits + cart_credits
    remaining_credits = credit_limit - total_used

    context = {
        'cart_items': cart_items,
        'cart_credits': cart_credits,
        'confirmed_credits': confirmed_credits,
        'credit_limit': credit_limit,
        'total_used': total_used,
        'remaining_credits': remaining_credits,
        'current_semester': current_semester,
        'over_limit': credit_limit > 0 and total_used > credit_limit,
    }

    return render(request, 'enrollment/cart.html', context)


def confirm_enrollment_view(request):
    if not request.user.is_authenticated or not request.user.is_student():
        return redirect('login')

    if request.method != 'POST':
        return redirect('cart')

    current_semester = request.user.current_semester

    if current_semester is None:
        messages.error(request, 'Your account has no semester assigned. Contact an administrator.')
        return redirect('cart')

    cart_items = CartItem.objects.filter(student=request.user).select_related('subject')

    if not cart_items.exists():
        messages.error(request, 'Your cart is empty. Add subjects before confirming.')
        return redirect('subject_catalog')

    confirmed_credits = Enrollment.objects.filter(
        student=request.user,
        status=Enrollment.STATUS_CONFIRMED,
        subject__semester=current_semester,
    ).aggregate(total=Sum('subject__credits'))['total'] or 0

    cart_credits = cart_items.aggregate(total=Sum('subject__credits'))['total'] or 0

    total_credits = confirmed_credits + cart_credits

    if total_credits > current_semester.credit_limit:
        messages.error(
            request,
            f'Enrollment blocked: {total_credits} total credits exceeds the '
            f'{current_semester.credit_limit}-credit limit for {current_semester.name}. '
            f'Remove some subjects from your cart.'
        )
        return redirect('cart')

    full_subjects = []
    for item in cart_items:
        if not item.subject.has_available_seats():
            full_subjects.append(item.subject.name)

    if full_subjects:
        messages.error(request, f'These subjects are full: {", ".join(full_subjects)}. Remove them from your cart.')
        return redirect('cart')

    item_count = cart_items.count()

    for item in cart_items:
        Enrollment.objects.get_or_create(
            student=request.user,
            subject=item.subject,
            defaults={'status': Enrollment.STATUS_CONFIRMED},
        )

    cart_items.delete()

    messages.success(request, f'Enrollment confirmed! You are now registered in {item_count} subject(s) ({cart_credits} credits).')
    return redirect('student_dashboard')


def student_dashboard_view(request):
    if not request.user.is_authenticated or not request.user.is_student():
        return redirect('login')

    current_semester = request.user.current_semester

    confirmed_enrollments = Enrollment.objects.filter(
        student=request.user,
        status=Enrollment.STATUS_CONFIRMED,
    ).select_related('subject', 'subject__semester', 'grade')

    total_confirmed_credits = confirmed_enrollments.aggregate(
        total=Sum('subject__credits')
    )['total'] or 0

    earned_credits = confirmed_enrollments.filter(
        grade__calculated_grade__gte=10
    ).aggregate(
        total=Sum('subject__credits')
    )['total'] or 0

    graded_enrollments = confirmed_enrollments.filter(
        grade__calculated_grade__isnull=False
    ).annotate(
        weighted_score=ExpressionWrapper(
            F('grade__calculated_grade') * F('subject__coefficient'),
            output_field=FloatField()
        )
    )

    agg = graded_enrollments.aggregate(
        total_weighted=Sum('weighted_score'),
        total_coefficient=Sum('subject__coefficient'),
    )

    weighted_average = None
    if agg['total_coefficient'] and agg['total_coefficient'] > 0:
        weighted_average = round(agg['total_weighted'] / agg['total_coefficient'], 2)

    cart_item_count = CartItem.objects.filter(student=request.user).count()

    context = {
        'current_semester': current_semester,
        'confirmed_enrollments': confirmed_enrollments,
        'total_confirmed_credits': total_confirmed_credits,
        'earned_credits': earned_credits,
        'weighted_average': weighted_average,
        'cart_item_count': cart_item_count,
    }

    return render(request, 'enrollment/student_dashboard.html', context)


def tutor_dashboard_view(request):
    if not request.user.is_authenticated or not request.user.is_tutor():
        return redirect('login')

    taught_subjects = Subject.objects.filter(
        responsible_tutor=request.user
    ).select_related('semester__specialization').annotate(
        confirmed_count=Count(
            'enrollments',
            filter=Q(enrollments__status='confirmed')
        ),
        graded_count=Count(
            'enrollments__grade',
            filter=Q(enrollments__grade__calculated_grade__isnull=False)
        ),
        avg_grade=Avg(
            'enrollments__grade__calculated_grade'
        ),
        pass_count=Count(
            'enrollments__grade',
            filter=Q(enrollments__grade__calculated_grade__gte=10)
        ),
    )

    context = {
        'taught_subjects': taught_subjects,
    }

    return render(request, 'enrollment/tutor_dashboard.html', context)


def subject_grades_view(request, subject_id):
    if not request.user.is_authenticated or not request.user.is_tutor():
        return redirect('login')

    subject = get_object_or_404(Subject, id=subject_id, responsible_tutor=request.user)

    enrollments = Enrollment.objects.filter(
        subject=subject,
        status=Enrollment.STATUS_CONFIRMED,
    ).select_related('student', 'grade').order_by('student__last_name', 'student__first_name')

    stats = Grade.objects.filter(
        enrollment__subject=subject,
        calculated_grade__isnull=False,
    ).aggregate(
        avg_grade=Avg('calculated_grade'),
        pass_count=Count('id', filter=Q(calculated_grade__gte=10)),
        fail_count=Count('id', filter=Q(calculated_grade__lt=10)),
        graded_count=Count('id'),
    )

    total_enrolled = enrollments.count()

    pass_rate = None
    if stats['graded_count'] and stats['graded_count'] > 0:
        pass_rate = round((stats['pass_count'] / stats['graded_count']) * 100, 1)

    context = {
        'subject': subject,
        'enrollments': enrollments,
        'stats': stats,
        'total_enrolled': total_enrolled,
        'pass_rate': pass_rate,
    }

    return render(request, 'enrollment/subject_grades.html', context)


def enter_grade_view(request, enrollment_id):
    if not request.user.is_authenticated or not request.user.is_tutor():
        return redirect('login')

    enrollment = get_object_or_404(
        Enrollment,
        id=enrollment_id,
        subject__responsible_tutor=request.user,
        status=Enrollment.STATUS_CONFIRMED,
    )

    grade_obj, created = Grade.objects.get_or_create(
        enrollment=enrollment,
        defaults={'session': Grade.SESSION_MAIN},
    )

    if request.method == 'POST':
        ds_raw = request.POST.get('continuous_assessment', '').strip()
        exam_raw = request.POST.get('final_exam', '').strip()
        session = request.POST.get('session', Grade.SESSION_MAIN)

        errors = []
        ds_value = None
        exam_value = None

        if ds_raw:
            try:
                ds_value = float(ds_raw)
                if not (0 <= ds_value <= 20):
                    errors.append('DS grade must be between 0 and 20.')
            except ValueError:
                errors.append('DS grade must be a valid number.')

        if exam_raw:
            try:
                exam_value = float(exam_raw)
                if not (0 <= exam_value <= 20):
                    errors.append('Exam grade must be between 0 and 20.')
            except ValueError:
                errors.append('Exam grade must be a valid number.')

        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            grade_obj.continuous_assessment = ds_value
            grade_obj.final_exam = exam_value
            grade_obj.session = session
            grade_obj.compute_grade()
            grade_obj.save()
            messages.success(request, f'Grade saved for {enrollment.student.get_full_name()}. Final: {grade_obj.calculated_grade}/20')
            return redirect('subject_grades', subject_id=enrollment.subject.id)

    context = {
        'enrollment': enrollment,
        'grade': grade_obj,
        'session_choices': Grade.SESSION_CHOICES,
    }

    return render(request, 'enrollment/enter_grade.html', context)
