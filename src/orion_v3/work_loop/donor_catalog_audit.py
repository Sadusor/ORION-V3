"""Classify donor catalog metadata without contacting any provider."""
from .cloud_family_selection import family


def classify(catalog):
    records = []
    for item in catalog.get('models', []):
        if not isinstance(item, dict):
            continue
        provider = str(item.get('provider') or '').lower()
        model = str(item.get('model') or '')
        group = family(model)
        if provider not in ('groq', 'gemini') or group == 'unknown':
            continue
        if any(word in model.lower() for word in ('preview', 'audio', 'tts', 'image', 'whisper', 'guard', 'speech', 'transcribe')):
            continue
        records.append({'provider': provider, 'model': model, 'family': group,
                        'catalog_available': item.get('available') is True,
                        'configured': bool(item.get('reviewer_id')),
                        'free_entitlement': 'UNVERIFIED'})
    return {'candidates': records, 'verified_free_families': [],
            'live_calls': 0, 'owner_approval': 'NOT_GRANTED'}
