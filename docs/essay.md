# Why create Eos?

Eos was born out of my work as Electoral Commissioner for the (now superseded) Reddit Model Australian Parliament [/r/ModelAustralia](https://reddit.com/r/ModelAustralia) in 2016. The previous Electoral Commissioner had been committed to election verifiability, and had implemented a simple [receipt-based system](https://www.quaxio.com/simple_auditable_anonymous_voting_scheme/). I wished to take this work to the next level, and cryptographic voting was the natural next step.

At the time, the only viable open-source solution was [Helios](https://github.com/benadida/helios-server). However, Helios is not developed particularly actively, and while its functionality is effective and well-tested, it does not support preferential voting – an absolute requirement for Australian elections – and to do so would require significant changes to the Helios internals, namely moving from homomorphic tallying to mixnet-based tallying.

To accomplish this, I combined Helios with a existing fork, [Zeus](https://github.com/grnet/zeus), to integrate preferential voting into a Helios [fork](https://github.com/RunasSudo/helios-server-mixnet), which I maintained for some time.

Eventually, however, it became obvious that this was an unmaintainable and inelegant solution. Helios as a piece of software is quite monolithic, control flowing backwards and forwards from file to file, making many assumptions about the nature of its data and process. This is by no means a criticism, but such a design did pose significant challenges when this data and process needed to be altered to fit preferential voting.

Zeus did so by splicing Helios together with another library, [PloneVoteCryptoLib](https://github.com/HRodriguez/svelib/tree/master/PloneVoteCryptoLib/plonevotecryptolib), and introducing some rudimentary abstraction into the Helios workflow, which was entirely functional, but created significant redundancy and complexity in the process – the same functionality could ostensibly be implemented in at seven places: the original Helios code, the modified code for homomorphic tallying, the modified code for mixnet tallying, each in both Python and Javascript, combined with the separate implementation from PloneVoteCryptoLib. This made debugging a nightmare.

Therefore, I took it on as a side project to create, from scratch, an open-source electronic voting web application that would address these shortcomings in my earlier project. This is Eos – Eos being, of course, the sister of Helios in Greek mythology.

Eos has been designed to be modular, with well-defined inter-module dependencies that allow for Eos to be extended to different voting systems and cryptographic protocols with greater ease than a monolithic system. As such, the core Eos components are built from an abstract perspective, making as few assumptions about its data as possible.

The *eos.core* module provides no election-related functionality whatsoever. Instead, it implements some of the key core functionality underpinning Eos, such as allowing objects to be converted between Python, JSON and database representations, and thereby safely hashed in a deterministic manner.

The *eos.base* module depends on *eos.core*, and provides basic election-related classes, implementing approval voting and plaintext votes, but is structured in such a way as to make as few assumptions as possible about these implementation details – the ballot construct, for example, making no assumptions about the structure of the ballot, and the encrypted ballot construct making no assumptions about the cryptosystem used.

The *eos.psr* module depends on *eos.base*, and is an example implementation of many of these specifics, implementing all constructs and processes required to run an election using a particular set of cryptographic techniques.

At this point, the *eos* module as a whole is a self-contained work, and could conceivably be used outside of *Eos* as a standalone library for elections, much like PloneVoteCryptoLib.

Finally, the *eosweb* module wraps around *eos*, and implements a web-based user interface for administering and voting in elections, and similar attempts have been made to abstract away the implementation specifics and allow the GUI to be easily extended to different systems.

At the same time, the duplication of code between Python and Javascript present in Helios has been addressed using [Transcrypt](https://github.com/QQuick/Transcrypt), so that the cryptographic operations and election-related constructs need only be implemented once in Python, and the Javascript version can automatically be transpiled from Python, facilitating unit testing and rapid development, and providing assurance that Python and Javascript implementations are equivalent. *eos.core* provides implementations on each platform for language-specific details like JSON and arbitrary precision integers, and so the remainder of the *eos* module is written in a language-agnostic way using the stubs in *eos.core*.

Helios, however, has definitely made many good design decisions, and many aspects of Eos are modelled on these. Most notably, Helios's long history is a testament to its stable and well-tested Python+Django+SQL stack, and following this example, we have endeavoured to choose actively-developed, well-supported, stable technologies for use in Eos whereever possible.

It must be noted, however, that the use case of Eos is rather different to that of Helios. Our use case has not changed since /r/ModelAustralia – very small low-stakes elections – so factors like scalability and enterprise-level security are of lesser concern. Eos is intended as a proof-of-concept to engage voters in the concept of verifiable voting, and so ease-of-use is of greater importance than cryptographic perfection – the exact opposite position to Helios, one imagines, being a project of academic interest. Indeed, deliberate design choices have been made to adopt cryptographic techniques known to be imperfect – such as Pedersen verifiable secret sharing, and reencryption-based random partial checking mixnets – due to the simplicity they afford while being ‘good enough’.

Most importantly, we recognise that the application of cryptography to verifiable electronic voting is an area of active research, and improved techniques will undoubtedly be found in future. It is here that we hope the value of Eos may be apparent, allowing such new techniques to be quickly adopted, without need to completely reimplement the entire stack from scratch.
