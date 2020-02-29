from xbox.scripts import pcap


def test_pcap_filter(pcap_filepath):
    packets = list(pcap.packet_filter(pcap_filepath))

    assert len(packets) == 26


def test_run_parser(pcap_filepath, crypto):
    pcap.parse(pcap_filepath, crypto)
