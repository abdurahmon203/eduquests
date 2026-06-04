from django.urls import reverse, NoReverseMatch

def eduquests_context(request):
    has_subjects = False
    subjects_url = '#'
    
    for url_name in ['subject_list', 'subjects', 'subjects:index', 'subjects:list']:
        try:
            subjects_url = reverse(url_name)
            has_subjects = True
            break
        except NoReverseMatch:
            continue
            
    return {
        'has_subjects_url': has_subjects,
        'subjects_url': subjects_url,
    }
