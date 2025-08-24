# Publishing to PyPI

## Prerequisites Completed ✅
- [x] Package structure ready
- [x] setup.py configured
- [x] pyproject.toml created
- [x] Distribution packages built

## Step 1: Create PyPI Account

1. Go to https://pypi.org/account/register/
2. Create an account with:
   - Username: (choose a unique username)
   - Email: info@toniwahrstaetter.com
   - Strong password

3. Verify your email address

## Step 2: Create API Token

1. Go to https://pypi.org/manage/account/token/
2. Create a new API token:
   - Token name: `eth-transaction-interceptor`
   - Scope: `Entire account` (for first upload)
3. **SAVE THE TOKEN** - you'll see it only once!
   - It starts with `pypi-...`

## Step 3: Configure Twine

Create `~/.pypirc` file:
```ini
[pypi]
username = __token__
password = pypi-YOUR-TOKEN-HERE
```

Or use environment variable:
```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-YOUR-TOKEN-HERE
```

## Step 4: Test with TestPyPI (Optional but Recommended)

1. Create TestPyPI account: https://test.pypi.org/account/register/
2. Get TestPyPI token: https://test.pypi.org/manage/account/token/
3. Upload to TestPyPI:
```bash
python -m twine upload --repository testpypi dist/*
```

4. Test installation:
```bash
pip install -i https://test.pypi.org/simple/ eth-transaction-interceptor
```

## Step 5: Upload to PyPI

### Check the package first:
```bash
twine check dist/*
```

### Upload to PyPI:
```bash
python -m twine upload dist/*
```

Or if using token directly:
```bash
python -m twine upload -u __token__ -p pypi-YOUR-TOKEN-HERE dist/*
```

## Step 6: Verify Installation

After upload, wait a few minutes, then:
```bash
pip install eth-transaction-interceptor
```

Test it works:
```bash
eth-interceptor --help
```

## Important Notes

### Package Name
- Current name: `eth-transaction-interceptor`
- Check availability: https://pypi.org/project/eth-transaction-interceptor/
- If taken, update name in setup.py and pyproject.toml

### Version Management
Before each release:
1. Update version in:
   - `setup.py`
   - `pyproject.toml`
   - `src/eth_interceptor/__init__.py`

2. Rebuild:
```bash
rm -rf dist/ build/ *.egg-info
python -m build
```

3. Upload new version:
```bash
python -m twine upload dist/*
```

### Security
- **NEVER** commit `.pypirc` or tokens to git
- Use environment variables in CI/CD
- Consider using GitHub Actions for automated releases

## GitHub Actions for Automated Release (Optional)

Create `.github/workflows/publish.yml`:
```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install build twine
    - name: Build package
      run: python -m build
    - name: Publish to PyPI
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
      run: twine upload dist/*
```

Then add your PyPI token as a GitHub secret:
1. Go to repo Settings → Secrets → Actions
2. Add new secret: `PYPI_API_TOKEN`
3. Value: your `pypi-...` token

## Troubleshooting

### "Package already exists"
- Increment version number
- Delete old builds: `rm -rf dist/ build/`
- Rebuild and upload

### "Invalid distribution"
Run checks:
```bash
twine check dist/*
python -m pip install -e .  # Test local install
```

### Authentication failed
- Verify token starts with `pypi-`
- Check token hasn't expired
- Ensure using `__token__` as username