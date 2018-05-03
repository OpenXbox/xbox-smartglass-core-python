Smartglass PCAP Analyzer
========================

Analyze sniffed network data in form of pcap.

NOTE: Scripts needs a shared secret to decrypt SmartGlass data!

Usage:
::

    usage: xbox-pcap [-h] file secret

    Parse PCAP files and show SG sessions

    positional arguments:
      file        Path to PCAP
      secret      Expanded secret for this session.

    optional arguments:
      -h, --help  show this help message and exit

Example:
::

    xbox-pcap packet_dump.pcap 00112233445566778899AABBCCEEFF001122334455667788
