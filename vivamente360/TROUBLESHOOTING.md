# Troubleshooting Guide

## URLconf Error: "The included URLconf '1' does not appear to have any patterns"

If you encounter this error:
```
django.core.exceptions.ImproperlyConfigured: The included URLconf '1' does not appear to have any patterns in it.
TypeError: 'int' object is not iterable
```

### Cause
This error is typically caused by corrupted Python cache files (*.pyc) or stale bytecode in the `__pycache__` directories.

### Solution

1. **Stop the development server** (Ctrl+C)

2. **Clear all Python cache files:**
   ```bash
   # From the project root directory
   find . -type d -name __pycache__ -exec rm -rf {} +
   find . -type f -name "*.pyc" -delete
   find . -type f -name "*.pyo" -delete
   ```

3. **Clear Django's cache (if using cache):**
   ```bash
   python manage.py clear_cache  # if django-extensions is installed
   # OR manually delete cache files/directories
   ```

4. **Restart the development server:**
   ```bash
   python manage.py runserver
   ```

### Additional Steps (if the problem persists)

5. **Check for circular imports:**
   - Review recent changes to URL configurations
   - Look for any imports in `urls.py` files that might create circular dependencies

6. **Verify URL configuration:**
   ```bash
   python manage.py check --deploy
   ```

7. **Check for uncommitted or untracked files:**
   ```bash
   git status
   git clean -fdx  # WARNING: This removes all untracked files!
   ```

8. **Reinstall dependencies:**
   ```bash
   pip install -r requirements.txt --force-reinstall --no-cache-dir
   ```

## Enhanced Logging

The project now includes enhanced HTTP request/response logging middleware that will help identify similar issues in the future.

### Logging Configuration

The middleware logs:
- **Request started**: Method, path, user, IP address
- **Request completed**: Status code, duration
- **Request exceptions**: Full exception details with stack trace

### Viewing Logs

Logs are written to:
- **Console**: Standard output (when running dev server)
- **File**: `logs/django.log`

### Log Levels

- **INFO**: Normal request/response flow
- **DEBUG**: Query parameters and detailed information
- **ERROR**: Exceptions and errors

### Example Log Output

```
INFO 2026-01-28 10:32:08 middleware Request started: GET /campaigns/ | User: admin | IP: 127.0.0.1
ERROR 2026-01-28 10:32:08 middleware Request exception: GET /campaigns/ | User: admin | Exception: ImproperlyConfigured: The included URLconf '1' does not appear to have any patterns in it.
INFO 2026-01-28 10:32:08 middleware Request completed: GET /campaigns/ | Status: 500 | Duration: 0.123s
```

## Common Issues and Solutions

### 1. Migration Conflicts
```bash
python manage.py migrate --fake-initial
```

### 2. Static Files Not Loading
```bash
python manage.py collectstatic --noinput
```

### 3. Database Connection Issues
- Check PostgreSQL is running
- Verify environment variables (DB_NAME, DB_USER, DB_PASSWORD)
- Check `config/settings/development.py` or `config/settings/production.py`

### 4. Template Rendering Errors
- Clear template cache
- Check Jinja2 configuration in `config/jinja2.py`
- Verify template syntax

## Getting Help

If the problem persists after trying these solutions:

1. **Check the logs** in `logs/django.log` for detailed error information
2. **Create an issue** with:
   - Full error traceback
   - Steps to reproduce
   - Recent changes made
   - Environment details (Python version, OS, etc.)

## Prevention

To prevent cache-related issues:

1. **Regular cleanup**: Add to your workflow
   ```bash
   # Add to .git/hooks/post-merge or run periodically
   find . -type d -name __pycache__ -exec rm -rf {} +
   ```

2. **Use .gitignore**: Ensure Python cache files are ignored
   ```
   __pycache__/
   *.py[cod]
   *$py.class
   ```

3. **Virtual environment**: Always use a virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate  # Windows
   ```
