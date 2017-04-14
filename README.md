# Eos

## Comparison with competitors

| | Helios | Eos
--- | --- | ---
Good | Yes | No
Eye Candy | No | Yes

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

## Crypto references

Crypto general knowledge:

* MENEZES, Alfred J., VAN OORSCHOT, Paul C. and VANSTONE, Scott A. *Handbook of Applied Cryptography*. CRC Press, 2001. Fifth printing. ISBN 978-0-8493-8523-0. Available from: http://cacr.uwaterloo.ca/hac/

Plaintext-aware (Chaum-Pedersen-Signed) ElGamal encryption:

* SEURIN, Yannick and TREGER, Joana. A Robust and Plaintext-Aware Variant of Signed ElGamal Encryption. In: *Cryptology ePrint Archive*. International Association for Cryptologic Research, 2012 [viewed 2017-01-27]. Revised 2013-02-25. Available from: http://ia.cr/2012/649
