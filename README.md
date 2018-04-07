# Eos: Modular verifiable elections

Work in progress – Both API and GUI are sufficiently complete to have seen experimental use

## Comparison with competitors

| | Helios | Eos
--- | --- | ---
Usable | Yes | Kinda
Good | Yes | Not really
Eye Candy | No | Yes!

![Screenshot](https://raw.githubusercontent.com/RunasSudo/Eos/master/docs/screenshot.png)

**Why create Eos?** – Read [here](docs/essay.md) for some background.

## Cryptographic details and references

Eos aims to be implementation-agnostic with respect to cryptographic details, with the included *eos.psr* package providing an example implementation.

For details of the implementation, refer to the [*Eos Voting Technical Report*](https://drive.google.com/open?id=1jjM5hkIBSZ8LryI12yPsuWv32Id7VjTC).

## Mother of all disclaimers

This is a fun side-project of mine, and should in no way be considered to be a serious attempt to build a production-ready election system suitable for real world deployment. Not even crypto experts are quite up to the task, and I am most certainly not a crypto expert, nor am I anything resembling a professional in any field even tangentially related to cryptographic elections.

I cannot guarantee the security of this implementation whatsoever. In fact, I would go so far as to guarantee that this software has so many holes it gives Swiss cheese a run for its money. That said, please feel free to roast Eos on the issue tracker!
