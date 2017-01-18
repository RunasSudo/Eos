# Eos

## Patching Django

If it is necessary to regenerate the patch:

```bash
git clone https://github.com/RunasSudo/django.git
cd django
git checkout 1.10.4 # The current version of Django used by Eos
git cherry-pick migrations-with-metaclasses
git format-patch --stdout HEAD~1 > /path/to/eos/patches/metaclass_migration.patch
```

To apply the patch:

```bash
patch -b -p1 -d 'venv/lib/python3.6/site-packages' < patches/metaclass_migration.patch
```

## EosObject notes

* `super()` is not supported
* `name` as an attribute is not supported
* `@classmethod` does not work correctly natively and requires a wrapper (until method decorators are implemented in Transcrypt)
