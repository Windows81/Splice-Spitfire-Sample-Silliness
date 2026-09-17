# _Sp!tFiR3_

Splice INSTRUMENT is a sample-based virtual instrument which can be downloaded as a plugin (VST3, AU, AAX) to be used directly in your digital audio workstation (DAW). Splice INSTRUMENT is free to download and use for anyone except for persons or entities located, organised, or resident in any jurisdiction subject to comprehensive U.S. trade sanctions, including Cuba, Iran, North Korea, Syria, and the Crimea and Donetsk People's Republic or Luhansk People's Republic regions of Ukraine.

I began working on this project on 2026-07-23. Using IDA Pro and x64dbg on Splice Instrument 3.4.18, I've reverse-engineered and re-implemented:

- File reader for `.spitfire` ([`./spitfire.py`](./spitfire.py); [`./samples/`](./samples/))
  - Buffer reader for encrypted `SFLC` subformat ([`./sflc.py`](./sflc.py); [`./samples/`](./samples/))
- Decryptor for `.zpreset` and `.zconfig` files ([`./zconfig.py`](./zconfig.py); [`./saved_presets.json`](./saved_presets.json))
- Retriever for content-library metadata ([`./search_content_lib.py`](./search_content_lib.py); [`./content_lib.json`](./content_lib.json))

LLMs were only used on this project in a consultory role as of 2026-09-17.
