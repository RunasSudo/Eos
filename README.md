# Eos: Verifiable elections

Work in progress – current development is focusing on an API for elections and cryptography, future work will be directed towards a functional user interface

## Comparison with competitors

| | Helios | Eos
--- | --- | ---
Usable | Yes | No
Good | Yes | No
Eye Candy | No | Heck No

## Cryptographic details and references

Eos aims to be implementation-agnostic with respect to cryptographic details. The included *eos.psr* package provides an example implementation with the following particulars:

* ElGamal encryption
  * MENEZES, Alfred J., Paul C. VAN OORSCHOT and Scott A. VANSTONE. *Handbook of Applied Cryptography*. CRC Press, 2001. Fifth printing. ISBN 978-0-8493-8523-0. Available from: http://cacr.uwaterloo.ca/hac/
* Distributed threshold ElGamal due to **P**edersen (1991) – planned
* **S**igned ElGamal due to Schnorr and Jakobsson (2000)
  * SCHNORR, Claus Peter and Markus JAKOBSSON. ‘Security of Signed ElGamal Encryption’. In: T. OKAMOTO, ed. *Advances in Cryptology – ASIACRYPT 2000*. Berlin: Springer-Verlag, 2000. pp. 73–89. Lecture Notes in Computer Science, vol. 1976. ISBN 978-3-540-44448-0. Available from: https://doi.org/10.1007/3-540-44448-3_7
* **R**andomised partial checking (RPC) due to Jakobsson, Juels and Rivest (2002)
  * JAKOBSSON, Markus, Ari JUELS and Ronald L. RIVEST. ‘Making Mix Nets Robust For Electronic Voting By Randomized Partial Checking’. In: *Proceedings of the 11th USENIX Security Symposium*. pp. 339–353. Berkeley: USENIX Association, 2002. Available from: https://www.usenix.org/event/sec02/full_papers/jakobsson/jakobsson.pdf
  * Taking note of points raised by Khazaei and Wikström (2013)
    * KHAZAEI, Shahram and Douglas WIKSTRÖM. ‘Randomized Partial Checking Revisited’. In: E. DAWSON, ed. *Topics in Cryptology – CT-RSA 2013*. Berlin: Springer-Verlag, 2013. pp. 115–128. Lecture Notes in Computer Science, vol. 7779. ISBN 978-3-642-36095-4. Available from: https://doi.org/10.1007/978-3-642-36095-4_8

## Mother of all disclaimers

This is a fun side-project of mine, and should in no way be considered to be a serious attempt to build a production-ready election system suitable for real world deployment. Not even crypto experts are quite up to the task, and I am most certainly not a crypto expert, nor am I anything resembling a professional in any field even tangentially related to cryptographic elections.

I cannot guarantee the security of this implementation whatsoever. In fact, I would go so far as to guarantee that this software has so many holes it gives Swiss cheese a run for its money. That said, please feel free to roast Eos on the issue tracker!
