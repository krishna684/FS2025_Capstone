# Multi-Language Support Usage Guide

## Overview
The AGBOT system now supports multi-language functionality with automatic language detection and localization for English, Spanish, Hindi, and Swahili.

## Supported Languages
- **English** (en) - Default
- **Spanish** (es) - Español
- **Hindi** (hi) - हिन्दी
- **Swahili** (sw) - Kiswahili

## Language Detection Priority

The system automatically detects the user's preferred language using the following priority:

1. **User Profile Language** (highest priority)
   - Set in user settings
   - Persisted in database
   - Applies to all sessions

2. **Session Language**
   - Set during current session
   - Overrides browser settings
   - Cleared on logout

3. **Browser Accept-Language Header**
   - Automatically detected from browser
   - No user action required
   - Falls back to English if unsupported

4. **Default to English** (lowest priority)
   - Used when no other language detected

## For Developers

### Getting Localized Pest Names

```python
from app import get_localized_pest_name

# Get pest name in user's language
pest_name = get_localized_pest_name(pest_id=1, language='es')
# Returns: "Escarabajo Japonés"

# Falls back to English if localized name not available
pest_name = get_localized_pest_name(pest_id=1, language='fr')
# Returns: "Japanese Beetle" (English fallback)
```

### Getting Translations

```python
from app import get_translation

# Get translation in specific language
greeting = get_translation('dashboard.greeting', 'hi')
# Returns: "नमस्ते, किसान!"

# Falls back to English if translation missing
text = get_translation('some.missing.key', 'es')
# Returns English version or key itself
# Logs missing translation to missing_translations.log
```

### In Templates

Templates automatically have access to translations via the `t` object:

```html
<!-- Simple translation -->
<h1>{{ t.dashboard.greeting }}</h1>

<!-- Nested translation -->
<p>{{ t.settings.profile }}</p>

<!-- Falls back to English automatically if translation missing -->
<span>{{ t.common.loading }}</span>
```

### In API Responses

```python
@app.route('/api/analyze', methods=['POST'])
@login_required
def analyze():
    # Get user's language preference
    lang = current_user.language if current_user.language else 'en'
    
    # Use localized pest name
    pest_name = get_localized_pest_name(pest.id, lang)
    
    # Return in response
    return jsonify({
        'pest_identified': pest_name,
        'language': lang
    })
```

### Detecting Browser Language

```python
from app import detect_browser_language

# In a route or view
with app.test_request_context(headers={'Accept-Language': 'es-ES,es;q=0.9'}):
    lang = detect_browser_language()
    # Returns: 'es'
```

## For Users

### Changing Language

1. **Via Settings Page**
   - Go to Settings → Preferences
   - Select your preferred language
   - Click "Save Changes"
   - Language persists across sessions

2. **Via API**
   ```javascript
   fetch('/api/update_language', {
       method: 'POST',
       headers: {
           'Content-Type': 'application/json'
       },
       body: JSON.stringify({
           language: 'es'
       })
   });
   ```

### Automatic Detection

The system automatically detects your browser's language:
- Chrome: Settings → Languages
- Firefox: Preferences → Language
- Safari: Preferences → Language
- Edge: Settings → Languages

## Database Schema

### Pest Names
```sql
CREATE TABLE pests (
    id SERIAL PRIMARY KEY,
    common_name VARCHAR(100) NOT NULL,      -- English
    scientific_name VARCHAR(100),
    name_es VARCHAR(100),                   -- Spanish
    name_hi VARCHAR(100),                   -- Hindi
    name_sw VARCHAR(100)                    -- Swahili
);
```

### Treatment Descriptions
```sql
CREATE TABLE treatments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,                       -- English
    description_es TEXT,                    -- Spanish
    description_hi TEXT,                    -- Hindi
    description_sw TEXT                     -- Swahili
);
```

### User Language Preference
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    language VARCHAR(10) DEFAULT 'en'      -- User's preferred language
);
```

## Translation Files

Translation files are located in `translations/` directory:
- `en.json` - English
- `es.json` - Spanish
- `hi.json` - Hindi
- `sw.json` - Swahili

### Adding New Translations

1. Edit the appropriate JSON file
2. Add your key-value pair:
   ```json
   {
       "section": {
           "key": "Translated text"
       }
   }
   ```
3. Restart the application

### Translation File Structure

```json
{
    "brand": {
        "name": "AGBOT",
        "tagline": "From Data to Harvest"
    },
    "dashboard": {
        "greeting": "Hi, Farmer!",
        "scanButton": "Scan New Leaf"
    }
}
```

## Missing Translation Handling

### Automatic Fallback
- Missing translations automatically fall back to English
- No error messages shown to users
- Seamless user experience

### Logging
- Missing translations logged to `missing_translations.log`
- Format: `[timestamp] Missing translation: key='...', language='...'`
- Review log periodically to add missing translations

### Example Log Entry
```
[2025-11-25 19:37:09] Missing translation: key='dashboard.newFeature', language='es'
```

## Testing

### Running Tests
```bash
python -m pytest test_language_support.py -v
```

### Running Demo
```bash
python demo_language_support.py
```

## Best Practices

1. **Always provide English translations** - Used as fallback
2. **Use descriptive keys** - e.g., `dashboard.greeting` not `d.g`
3. **Keep translations consistent** - Same tone across languages
4. **Test with real users** - Native speakers validate translations
5. **Monitor missing_translations.log** - Add missing translations regularly

## Common Issues

### Issue: Language not changing
**Solution**: Check priority order. User profile overrides all other settings.

### Issue: Pest names showing in English
**Solution**: Ensure localized names exist in database. Check `name_es`, `name_hi`, `name_sw` columns.

### Issue: Translations not updating
**Solution**: Restart application after modifying translation files.

### Issue: Browser language not detected
**Solution**: Check browser's Accept-Language header is set correctly.

## API Endpoints

### Update Language
```
POST /api/update_language
Content-Type: application/json

{
    "language": "es"
}
```

**Response:**
```json
{
    "message": "Language updated successfully"
}
```

## Support

For issues or questions about multi-language support:
1. Check this guide
2. Review `missing_translations.log`
3. Run test suite to verify functionality
4. Check browser console for errors

## Future Enhancements

Potential future additions:
- Right-to-left (RTL) language support (Arabic, Hebrew)
- Regional variants (en-US vs en-GB)
- Dynamic translation loading
- Translation management interface
- Crowdsourced translations
- Machine translation integration
